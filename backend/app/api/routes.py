import hashlib
import json
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.application.actions import ActionService
from app.config import get_settings
from app.domain.contracts import (
    MUNICIPALITIES,
    ActionInput,
    BeneficiaryInput,
    ImportConfirmation,
    Login,
    Professional,
    Version,
)
from app.infrastructure.actions import (
    SqlActionsRepository,
    action_or_404,
    add_beneficiary,
    audit,
    cipher,
    enqueue,
    snapshot,
)
from app.infrastructure.database import get_engine, get_identity_engine
from app.infrastructure.identity import IdentityRepository, verify_password
from app.infrastructure.import_files import analyze_pdf, document_for
from app.infrastructure.imports import metadata, render_page
from app.infrastructure.models import (
    Action,
    Audit,
    Beneficiary,
    ImportBatch,
    ImportDocument,
    Outbox,
    Participation,
    SessionRecord,
)
from app.security.session import (
    COOKIE,
    clear_login_failures,
    consume_login,
    create_session,
    csrf,
    current_professional,
    digest,
    enforce_origin,
    identities,
    technologist,
    writer,
)

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict:
    return {"status": "API_OK", "versao": "0.1.0"}


@router.post("/auth/login", status_code=204)
def login(
    data: Login,
    request: Request,
    response: Response,
    repository: IdentityRepository = Depends(identities),
):
    enforce_origin(request)
    consume_login(data.identifier.lower(), request.client.host if request.client else "unknown")
    result = repository.find(data.identifier.lower())
    valid = verify_password(data.password.get_secret_value(), result[1] if result else "")
    if not result or not valid:
        raise HTTPException(401, "Não foi possível entrar com essas credenciais.")
    if not result[0].allowed:
        raise HTTPException(
            403,
            "Acesso restrito a profissionais administrativos das equipes Administração ou Tecnologia.",
        )
    clear_login_failures(data.identifier.lower())
    token = create_session(result[0])
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=get_settings().production,
        samesite="strict",
        max_age=8 * 3600,
        path="/",
    )


@router.get("/auth/me")
def me(request: Request, professional: Professional = Depends(current_professional)):
    return {
        **professional.model_dump(),
        "csrf_token": csrf(request.cookies[COOKIE]),
        "agenda_url": get_settings().agenda_web_url,
    }


@router.post("/auth/logout", status_code=204)
def logout(request: Request, response: Response, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        session.execute(
            delete(SessionRecord).where(SessionRecord.token_hash == digest(request.cookies[COOKIE]))
        )
        audit(session, professional, "auth.logout", professional.profissional_id)
    response.delete_cookie(
        COOKIE, path="/", httponly=True, secure=get_settings().production, samesite="strict"
    )


@router.get("/localidades/pb")
def municipalities(_professional: Professional = Depends(current_professional)):
    return [
        {"codigo": code, "nome": name}
        for code, name in sorted(MUNICIPALITIES.items(), key=lambda item: item[1])
    ]


@router.get("/acoes")
def list_actions(
    busca: str = Query("", max_length=160),
    municipio: str = "",
    status: str = "",
    categoria: str = "",
    inicio: str = "",
    fim: str = "",
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(10, ge=1, le=100),
    _professional: Professional = Depends(current_professional),
):
    with Session(get_engine()) as session:
        query = select(Action).order_by(Action.criado_em.desc(), Action.id)
        if busca:
            query = query.where(Action.nome.icontains(busca, autoescape=True))
        if status:
            query = query.where(Action.status == status)
        if categoria:
            query = query.where(Action.categoria == categoria)
        if inicio:
            query = query.where(Action.inicio_em >= inicio)
        if fim:
            query = query.where(Action.inicio_em <= fim)
        rows = session.scalars(query).all()
        if municipio:
            rows = [
                row for row in rows if any(p["municipio_ibge"] == municipio for p in row.locais)
            ]
        total = len(rows)
        return {
            "items": [
                snapshot(session, row) for row in rows[(pagina - 1) * tamanho : pagina * tamanho]
            ],
            "total": total,
            "pagina": pagina,
            "tamanho": tamanho,
        }


@router.post("/acoes", status_code=201)
def create(data: ActionInput, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        return ActionService(SqlActionsRepository(session)).save(data, professional)


@router.get("/acoes/{identifier}")
def detail(identifier: str, professional: Professional = Depends(current_professional)):
    with Session(get_engine()) as session, session.begin():
        row = action_or_404(session, identifier)
        history = session.scalars(
            select(Audit).where(Audit.entidade_id == identifier).order_by(Audit.criado_em.desc())
        ).all()
        audit(session, professional, "acoes.read", identifier)
        return {
            **snapshot(session, row),
            "historico": [
                {"operacao": item.operacao, "criado_em": item.criado_em} for item in history
            ],
        }


@router.patch("/acoes/{identifier}")
def edit(identifier: str, data: ActionInput, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        return ActionService(SqlActionsRepository(session)).save(data, professional, identifier)


@router.delete("/acoes/{identifier}")
def archive(identifier: str, data: Version, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        return ActionService(SqlActionsRepository(session)).transition(
            identifier, data.versao, "arquivada", professional
        )


@router.post("/acoes/{identifier}/revisar")
def review(identifier: str, data: Version, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        return ActionService(SqlActionsRepository(session)).transition(
            identifier, data.versao, "em_revisao", professional
        )


@router.post("/acoes/{identifier}/aprovar")
def approve(identifier: str, data: Version, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        return ActionService(SqlActionsRepository(session)).transition(
            identifier, data.versao, "validada", professional
        )


@router.post("/acoes/{identifier}/publicar")
def publish(identifier: str, data: Version, professional: Professional = Depends(writer)):
    # Reserva a etapa; não permite aparentar publicação no Portal sem integração.
    raise HTTPException(503, "Publicação aguarda contrato e aprovação institucional da integração.")


@router.get("/acoes/{identifier}/beneficiarios")
def beneficiaries(
    identifier: str,
    pagina: int = Query(1, ge=1),
    professional: Professional = Depends(current_professional),
):
    with Session(get_engine()) as session, session.begin():
        action_or_404(session, identifier)
        query = (
            select(Beneficiary, Participation)
            .join(Participation)
            .where(Participation.acao_id == identifier)
        )
        total = session.scalar(
            select(func.count())
            .select_from(Participation)
            .where(Participation.acao_id == identifier)
        )
        rows = session.execute(
            query.order_by(Participation.id).offset((pagina - 1) * 20).limit(20)
        ).all()
        items = []
        for person, participation in rows:
            data = json.loads(cipher().decrypt(person.dados_cifrados.encode()))
            if data["id"] != person.id:
                raise HTTPException(503, "Falha na integridade do cadastro.")
            items.append(
                {
                    "id": person.id,
                    "nome": data["nome"],
                    "municipio_residencia_ibge": person.municipio_residencia_ibge,
                    "local_indice": participation.local_indice,
                }
            )
        audit(session, professional, "beneficiarios.read", identifier)
        return {"items": items, "total": total, "pagina": pagina}


@router.post("/acoes/{identifier}/beneficiarios", status_code=201)
def beneficiary(
    identifier: str, data: BeneficiaryInput, professional: Professional = Depends(writer)
):
    with Session(get_engine()) as session, session.begin():
        session.scalar(select(Action).where(Action.id == identifier).with_for_update())
        result = add_beneficiary(session, identifier, data, professional)
        row = action_or_404(session, identifier)
        row.versao += 1
        row.status = "rascunho"
        row.aprovado_por = row.publicado_por = None
        row.atualizado_em = datetime.now(UTC)
        session.flush()
        enqueue(session, row)
        return {"status": result}


@router.get("/indicadores")
def indicators(_professional: Professional = Depends(current_professional)):
    with Session(get_engine()) as session:
        rows = session.scalars(select(Action).where(Action.status != "arquivada")).all()
        ids = [row.id for row in rows]
        count = (
            session.scalar(
                select(func.count())
                .select_from(Participation)
                .where(Participation.acao_id.in_(ids))
            )
            or 0
        )
        municipalities = {}
        for row in rows:
            for code in {p["municipio_ibge"] for p in row.locais}:
                municipalities[code] = municipalities.get(code, 0) + 1
        return {
            "acoes": len(rows),
            "participacoes": count,
            "municipios": len(municipalities),
            "em_revisao": sum(row.status == "em_revisao" for row in rows),
            "por_municipio": [
                {"codigo": code, "nome": MUNICIPALITIES[code], "acoes": total}
                for code, total in sorted(municipalities.items(), key=lambda p: -p[1])
            ],
            "atualizado_em": datetime.now(UTC),
            "escopo": "ações não arquivadas, todo o período",
        }


@router.post("/importacoes/preview")
def preview(professional: Professional = Depends(writer)):
    source_hash, pages = metadata()
    with Session(get_engine()) as session, session.begin():
        batch = ImportBatch(
            hash_arquivo=source_hash, paginas=pages, autor_id=professional.profissional_id
        )
        session.add(batch)
        session.flush()
        audit(session, professional, "importacoes.preview", batch.id)
        return {
            "id": batch.id,
            "paginas": pages,
            "documento": "Melhor VISÃO",
            "avisos": [
                "Documento sem transcrição automática. Confira cada página.",
                "Campos ópticos não serão importados.",
                "Sem deduplicação automática por nome.",
            ],
        }


def require_batch(session: Session, identifier: str, professional: Professional) -> ImportBatch:
    batch = session.get(ImportBatch, identifier)
    if not batch or batch.autor_id != professional.profissional_id:
        raise HTTPException(404, "Importação não encontrada.")
    if (datetime.now(UTC) - batch.criado_em.replace(tzinfo=UTC)).total_seconds() > 86400:
        raise HTTPException(410, "Prévia expirada. Prepare o documento novamente.")
    return batch


@router.get("/importacoes/{identifier}/paginas/{page}")
def page_preview(
    identifier: str,
    page: int,
    rotacao: int = Query(0, ge=0, le=270, multiple_of=90),
    professional: Professional = Depends(current_professional),
):
    with Session(get_engine()) as session, session.begin():
        batch = require_batch(session, identifier, professional)
        if not 1 <= page <= batch.paginas:
            raise HTTPException(404, "Página não encontrada.")
        audit(session, professional, "importacoes.page", identifier)
        if session.get(ImportDocument, identifier):
            _, document = document_for(session, identifier, professional)
            if document.formato != "pdf":
                raise HTTPException(422, "Este arquivo possui registros tabulares.")
            content = cipher().decrypt(document.conteudo_cifrado.encode())
            return Response(
                analyze_pdf(content, page, rotacao),
                media_type="image/jpeg",
                headers={"Cache-Control": "no-store"},
            )
    return Response(
        render_page(page), media_type="image/png", headers={"Cache-Control": "no-store"}
    )


@router.post("/importacoes/confirmar")
def confirm(data: ImportConfirmation, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        batch = require_batch(session, data.importacao_id, professional)
        uploaded = session.get(ImportDocument, batch.id)
        if get_settings().production:
            if not uploaded:
                raise HTTPException(503, "Selecione e revise um arquivo na área Importar dados.")
            if not data.confirmacao_producao:
                raise HTTPException(422, "Confirme expressamente a importação em produção.")
        if uploaded:
            document_for(session, batch.id, professional)
        session.scalar(select(Action).where(Action.id == data.acao_id).with_for_update())
        row = action_or_404(session, data.acao_id)
        included = existing = 0
        for record in data.registros:
            if record.pagina > batch.paginas:
                raise HTTPException(422, "Página fora do documento.")
            source = hashlib.sha256(
                f"{batch.hash_arquivo}:{record.pagina}:{row.id}".encode()
            ).hexdigest()
            result = add_beneficiary(
                session,
                row.id,
                BeneficiaryInput(**record.model_dump(exclude={"pagina", "revisado"})),
                professional,
                source,
            )
            included += result == "incluido"
            existing += result == "existente"
        if included:
            row.versao += 1
            row.status = "rascunho"
            row.aprovado_por = row.publicado_por = None
            row.atualizado_em = datetime.now(UTC)
            session.flush()
            enqueue(session, row)
        audit(session, professional, "importacoes.confirmar", batch.id)
        sources = [
            hashlib.sha256(f"{batch.hash_arquivo}:{page}:{row.id}".encode()).hexdigest()
            for page in range(1, batch.paginas + 1)
        ]
        processed = session.scalar(
            select(func.count()).select_from(Participation).where(Participation.origem.in_(sources))
        )
        return {
            "incluidos": included,
            "existentes": existing,
            "pendentes": batch.paginas - processed,
        }


@router.get("/tecnologia/saude")
def technical_health(_professional: Professional = Depends(technologist)):
    started = time.monotonic()
    status = "DB_ERRO"
    try:
        with get_identity_engine().connect() as connection:
            if connection.scalar(text("SELECT 1")) == 1:
                status = "DB_OK"
    except (SQLAlchemyError, RuntimeError, ValueError):
        status = "DB_ERRO"
    with Session(get_engine()) as session:
        pending = session.scalar(
            select(func.count()).select_from(Outbox).where(Outbox.status != "entregue")
        )
        delivered = session.scalar(select(func.max(Outbox.enviado_em)))
    config = get_settings()
    return {
        "banco": status,
        "latencia_ms": round((time.monotonic() - started) * 1000),
        "api": "API_OK",
        "armazenamento": "PostgreSQL institucional / actions_map"
        if config.production
        else "local isolado",
        "agenda": "CONFIG_PENDENTE" if not config.agenda_summaries_url else "NAO_VERIFICADA",
        "fila_pendente": pending,
        "ultima_confirmacao": delivered,
        "verificado_em": datetime.now(UTC),
        "credencial": {
            "alias": "agenda-resumos",
            "escopo": "acoes.resumos.write",
            "status": "configurada"
            if config.agenda_service_token.get_secret_value()
            else "ausente",
        },
    }
