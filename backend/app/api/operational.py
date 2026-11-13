"""Área operacional: nenhuma dependência de permissão administrativa implícita."""

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.clinical import ClinicalDesignationInput, ClinicalInput, ClinicalView
from app.domain.contracts import (
    MUNICIPALITIES,
    BeneficiaryInput,
    BeneficiarySheet,
    BeneficiaryUpdate,
    Login,
    Professional,
)
from app.domain.operational import OperationalAccountInput, OperationalAccountView
from app.infrastructure.actions import add_beneficiary, audit, cipher, enqueue
from app.infrastructure.beneficiaries import SqlBeneficiariesRepository
from app.infrastructure.beneficiary_data import decode_beneficiary
from app.infrastructure.clinical import SqlClinicalRepository
from app.infrastructure.database import get_engine
from app.infrastructure.identity import IdentityRepository, verify_password
from app.infrastructure.models import (
    Action,
    ActionLogo,
    Beneficiary,
    ClinicalDesignation,
    InstitutionLogo,
    OperationalAccount,
    OperationalSession,
    Participation,
    StaffAssignment,
    StaffRecord,
)
from app.infrastructure.operational_access import (
    account_view,
    action_scope,
    operator_actor,
    person_scope,
    require_location,
    require_operational_enabled,
    save_account,
    staff_identity,
)
from app.security.operational import (
    current_operator,
    operational_cookie,
    operational_writer,
    revoke_operator_session,
)
from app.security.session import (
    clear_login_failures,
    consume_login,
    csrf,
    current_professional,
    digest,
    enforce_origin,
    identities,
    writer,
)

router = APIRouter(prefix="/api/v1")


@router.get("/profissionais/{staff_id}/acesso", response_model=OperationalAccountView)
def read_account(staff_id: UUID, actor: Professional = Depends(current_professional)):
    require_operational_enabled()
    with Session(get_engine()) as session, session.begin():
        if not session.get(StaffRecord, str(staff_id)):
            raise HTTPException(404, "Profissional não encontrado.")
        row = session.scalar(
            select(OperationalAccount).where(OperationalAccount.profissional_id == str(staff_id))
        )
        audit(session, actor, "operacional.conta.read", str(staff_id))
        return account_view(row)


@router.put("/profissionais/{staff_id}/acesso", response_model=OperationalAccountView)
def manage_account(
    staff_id: UUID,
    data: OperationalAccountInput,
    request: Request,
    actor: Professional = Depends(writer),
    repository: IdentityRepository = Depends(identities),
):
    require_operational_enabled()
    key = "operational-reauth:" + actor.profissional_id
    consume_login(key, request.client.host if request.client else "unknown")
    found = repository.find(actor.profissional_id, by_id=True)
    valid = verify_password(data.senha_institucional.get_secret_value(), found[1] if found else "")
    if not found or not found[0].allowed or not valid:
        raise HTTPException(401, "Confirme sua senha institucional para gerenciar acessos.")
    clear_login_failures(key)
    with Session(get_engine()) as session, session.begin():
        return save_account(session, str(staff_id), data, actor)


@router.post("/operacao/auth/login", status_code=204)
def login_operator(data: Login, request: Request, response: Response):
    require_operational_enabled()
    enforce_origin(request)
    name = data.identifier.strip().lower()
    limit_key = "operational-login:" + name
    consume_login(limit_key, request.client.host if request.client else "unknown")
    with Session(get_engine()) as session, session.begin():
        found = session.execute(
            select(OperationalAccount, StaffRecord)
            .join(
                StaffRecord,
                StaffRecord.id == OperationalAccount.profissional_id,
            )
            .where(OperationalAccount.usuario == name)
        ).first()
        if found:
            staff = session.get(
                StaffRecord, found[1].id, with_for_update=True, populate_existing=True
            )
            account = session.get(
                OperationalAccount, found[0].id, with_for_update=True, populate_existing=True
            )
            found = (account, staff) if account and staff and account.usuario == name else None
        valid = verify_password(
            data.password.get_secret_value(), found[0].senha_hash if found else ""
        )
        if not found or not valid:
            raise HTTPException(401, "Não foi possível entrar com essas credenciais.")
        actor = operator_actor(*found)
        token = secrets.token_urlsafe(32)
        session.execute(
            delete(OperationalSession).where(OperationalSession.expires_at <= datetime.now(UTC))
        )
        # Evita acumular sessões antigas da mesma conta a cada novo login.
        session.execute(
            delete(OperationalSession).where(OperationalSession.conta_id == found[0].id)
        )
        session.add(
            OperationalSession(
                token_hash=digest(token),
                conta_id=found[0].id,
                expires_at=datetime.now(UTC) + timedelta(hours=8),
            )
        )
        audit(session, actor, "operacional.login", found[0].id)
    clear_login_failures(limit_key)
    response.set_cookie(
        operational_cookie(request),
        token,
        httponly=True,
        secure=get_settings().production,
        samesite="strict",
        max_age=8 * 3600,
        path="/",
    )


@router.get("/operacao/auth/me")
def me_operator(request: Request, actor: Professional = Depends(current_operator)):
    return {
        **actor.model_dump(),
        "agenda_url": "",
        "csrf_token": csrf(request.cookies[operational_cookie(request)]),
        "demonstracao": getattr(request.app.state, "demonstracao", False),
    }


@router.post("/operacao/auth/logout", status_code=204)
def logout_operator(
    request: Request, response: Response, actor: Professional = Depends(operational_writer)
):
    with Session(get_engine()) as session, session.begin():
        revoke_operator_session(session, request.cookies[operational_cookie(request)])
        audit(session, actor, "operacional.logout", actor.staff_id)
    response.delete_cookie(
        operational_cookie(request),
        path="/",
        httponly=True,
        secure=get_settings().production,
        samesite="strict",
    )


@router.get("/operacao/localidades/pb")
def localities(_actor: Professional = Depends(current_operator)):
    return [
        {"codigo": code, "nome": name}
        for code, name in sorted(MUNICIPALITIES.items(), key=lambda item: item[1])
    ]


def operational_action(action, assignment):
    return {
        "id": action.id,
        "nome": action.nome,
        "inicio_em": action.inicio_em,
        "fim_em": action.fim_em,
        "institucional": action.institucional,
        "locais": [
            {**place, "indice": index, "municipio_nome": MUNICIPALITIES[place["municipio_ibge"]]}
            for index, place in enumerate(action.locais)
            if assignment.locais_indices is None or index in assignment.locais_indices
        ],
    }


@router.get("/operacao/acoes")
def assigned_actions(pagina: int = Query(1, ge=1), actor: Professional = Depends(current_operator)):
    with Session(get_engine()) as session, session.begin():
        query = (
            select(Action, StaffAssignment)
            .join(StaffAssignment)
            .where(
                StaffAssignment.profissional_id == actor.staff_id,
                StaffAssignment.ativo.is_(True),
                StaffAssignment.papel
                == ("RECEPCAO" if actor.categoria == "RECEPCAO" else "PROFISSIONAL"),
                Action.status != "arquivada",
            )
        )
        total = session.scalar(select(func.count()).select_from(query.subquery()))
        rows = session.execute(
            query.order_by(Action.inicio_em.desc(), Action.id).offset((pagina - 1) * 20).limit(20)
        ).all()
        audit(session, actor, "operacional.acoes.read", actor.staff_id)
        return {
            "items": [operational_action(*row) for row in rows],
            "total": total,
            "pagina": pagina,
        }


@router.get("/operacao/acoes/{action_id}")
def assigned_action(action_id: UUID, actor: Professional = Depends(current_operator)):
    with Session(get_engine()) as session, session.begin():
        action, assignment = action_scope(session, str(action_id), actor)
        audit(session, actor, "operacional.acao.read", str(action_id))
        return operational_action(action, assignment)


def people_query(action_id, actor, assignment):
    query = (
        select(Beneficiary, Participation)
        .join(Participation)
        .where(Participation.acao_id == action_id)
    )
    if assignment.locais_indices is not None:
        query = query.where(Participation.local_indice.in_(assignment.locais_indices))
    if actor.categoria != "RECEPCAO":
        query = query.join(ClinicalDesignation).where(
            ClinicalDesignation.ativo.is_(True),
            ClinicalDesignation.profissional_id == actor.staff_id,
            ClinicalDesignation.identidade_id == actor.profissional_id,
        )
    return query


@router.get("/operacao/acoes/{action_id}/beneficiarios")
def assigned_people(
    action_id: UUID, pagina: int = Query(1, ge=1), actor: Professional = Depends(current_operator)
):
    with Session(get_engine()) as session, session.begin():
        _, assignment = action_scope(session, str(action_id), actor)
        query = people_query(str(action_id), actor, assignment)
        total = session.scalar(select(func.count()).select_from(query.subquery()))
        rows = session.execute(
            query.order_by(Participation.id).offset((pagina - 1) * 20).limit(20)
        ).all()
        audit(session, actor, "operacional.atendimentos.read", str(action_id))
        return {
            "items": [
                {
                    "id": person.id,
                    "nome": decode_beneficiary(person, cipher())[0].nome,
                    "local_indice": participation.local_indice,
                }
                for person, participation in rows
            ],
            "total": total,
            "pagina": pagina,
        }


@router.post("/operacao/acoes/{action_id}/beneficiarios", status_code=201)
def register_person(
    action_id: UUID,
    data: BeneficiaryInput,
    request: Request,
    actor: Professional = Depends(operational_writer),
):
    try:
        key = str(UUID(request.headers.get("idempotency-key", "")))
    except ValueError:
        raise HTTPException(400, "Identificador da operação ausente. Reabra o cadastro.") from None
    with Session(get_engine()) as session, session.begin():
        action, assignment = action_scope(session, str(action_id), actor, reception=True)
        require_location(action, assignment, data.local_indice)
        source = hashlib.sha256(
            f"local:{actor.profissional_id}:{action_id}:{key}".encode()
        ).hexdigest()
        result = add_beneficiary(session, str(action_id), data, actor, source)
        if result == "incluido":
            action.versao += 1
            action.status = "em_revisao"
            action.aprovado_por = action.publicado_por = None
            action.atualizado_em = datetime.now(UTC)
            session.flush()
            enqueue(session, action)
        return {"resultado": result}


def general_sheet(session, action_id, person_id, actor, second_copy=False):
    person_scope(session, action_id, person_id, actor)
    if actor.categoria != "RECEPCAO":
        SqlClinicalRepository(session, actor).find(action_id, person_id)
    return SqlBeneficiariesRepository(session).read(action_id, person_id, actor, second_copy)


@router.get(
    "/operacao/acoes/{action_id}/beneficiarios/{person_id}", response_model=BeneficiarySheet
)
def read_person(action_id: UUID, person_id: UUID, actor: Professional = Depends(current_operator)):
    with Session(get_engine()) as session, session.begin():
        return general_sheet(session, str(action_id), str(person_id), actor)


@router.get(
    "/operacao/acoes/{action_id}/beneficiarios/{person_id}/segunda-via",
    response_model=BeneficiarySheet,
)
def reprint_person(
    action_id: UUID, person_id: UUID, actor: Professional = Depends(current_operator)
):
    with Session(get_engine()) as session, session.begin():
        return general_sheet(session, str(action_id), str(person_id), actor, True)


@router.patch(
    "/operacao/acoes/{action_id}/beneficiarios/{person_id}", response_model=BeneficiarySheet
)
def edit_person(
    action_id: UUID,
    person_id: UUID,
    data: BeneficiaryUpdate,
    actor: Professional = Depends(operational_writer),
):
    with Session(get_engine()) as session, session.begin():
        action, assignment, _ = person_scope(
            session, str(action_id), str(person_id), actor, reception=True
        )
        require_location(action, assignment, data.local_indice)
        return SqlBeneficiariesRepository(session).update(
            str(action_id), str(person_id), data, actor
        )


@router.get("/operacao/acoes/{action_id}/profissionais")
def eligible_staff(action_id: UUID, actor: Professional = Depends(current_operator)):
    with Session(get_engine()) as session, session.begin():
        _, own_assignment = action_scope(session, str(action_id), actor, reception=True)
        rows = session.execute(
            select(StaffRecord, StaffAssignment)
            .join(StaffAssignment)
            .where(
                StaffAssignment.acao_id == str(action_id),
                StaffAssignment.ativo.is_(True),
                StaffAssignment.papel == "PROFISSIONAL",
                StaffRecord.ativo.is_(True),
                StaffRecord.habilitacao_validada.is_(True),
                StaffRecord.registro_clinico_autorizado.is_(True),
            )
        ).all()
        return [
            {
                "id": staff.id,
                "nome": staff.nome,
                "categoria": staff.categoria,
                "locais_indices": assignment.locais_indices,
            }
            for staff, assignment in rows
            if staff_identity(session, staff)
            and (
                own_assignment.locais_indices is None
                or assignment.locais_indices is None
                or set(own_assignment.locais_indices) & set(assignment.locais_indices)
            )
        ]


@router.put("/operacao/acoes/{action_id}/beneficiarios/{person_id}/designacao-clinica")
def assign_case(
    action_id: UUID,
    person_id: UUID,
    data: ClinicalDesignationInput,
    actor: Professional = Depends(operational_writer),
):
    with Session(get_engine()) as session, session.begin():
        person_scope(session, str(action_id), str(person_id), actor, reception=True)
        return SqlClinicalRepository(session, actor).designation(
            str(action_id), str(person_id), data
        )


@router.get("/operacao/acoes/{action_id}/beneficiarios/{person_id}/designacao-clinica")
def case_designation(
    action_id: UUID, person_id: UUID, actor: Professional = Depends(current_operator)
):
    with Session(get_engine()) as session, session.begin():
        person_scope(session, str(action_id), str(person_id), actor, reception=True)
        return SqlClinicalRepository(session, actor).designation(str(action_id), str(person_id))


@router.get(
    "/operacao/acoes/{action_id}/beneficiarios/{person_id}/clinica", response_model=ClinicalView
)
def clinical_read(
    action_id: UUID,
    person_id: UUID,
    versao: int | None = Query(None, ge=1),
    actor: Professional = Depends(current_operator),
):
    with Session(get_engine()) as session, session.begin():
        return SqlClinicalRepository(session, actor).read(str(action_id), str(person_id), versao)


@router.put(
    "/operacao/acoes/{action_id}/beneficiarios/{person_id}/clinica", response_model=ClinicalView
)
def clinical_save(
    action_id: UUID,
    person_id: UUID,
    data: ClinicalInput,
    actor: Professional = Depends(operational_writer),
):
    with Session(get_engine()) as session, session.begin():
        return SqlClinicalRepository(session, actor).save(str(action_id), str(person_id), data)


@router.get("/operacao/acoes/{action_id}/marcas/{logo_id}")
def action_logo(action_id: UUID, logo_id: UUID, actor: Professional = Depends(current_operator)):
    with Session(get_engine()) as session, session.begin():
        action_scope(session, str(action_id), actor)
        logo = session.get(ActionLogo, str(logo_id))
        if not logo or logo.acao_id != str(action_id):
            raise HTTPException(404, "Marca não encontrada nesta ação.")
        audit(session, actor, "operacional.marca.read", str(logo_id))
        return Response(base64.b64decode(logo.conteudo_base64), media_type="image/png")


@router.get("/operacao/acoes/{action_id}/instituicoes/{institution_id}/marcas/{logo_id}")
def institution_logo(
    action_id: UUID,
    institution_id: UUID,
    logo_id: UUID,
    actor: Professional = Depends(current_operator),
):
    with Session(get_engine()) as session, session.begin():
        action, _ = action_scope(session, str(action_id), actor)
        links = action.institucional.get("contratantes", []) + action.institucional.get(
            "apoiadores", []
        )
        if not any(
            link.get("instituicao_id") == str(institution_id)
            and link.get("logo_id") == str(logo_id)
            and link.get("uso_autorizado")
            for link in links
        ):
            raise HTTPException(404, "Marca não encontrada nesta ação.")
        logo = session.get(InstitutionLogo, str(logo_id))
        if not logo or logo.instituicao_id != str(institution_id):
            raise HTTPException(404, "Marca não encontrada nesta ação.")
        audit(session, actor, "operacional.marca.read", str(logo_id))
        return Response(base64.b64decode(logo.conteudo_base64), media_type="image/png")
