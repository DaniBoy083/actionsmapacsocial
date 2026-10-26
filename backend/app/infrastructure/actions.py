import json
from datetime import UTC, datetime
from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.contracts import (
    MUNICIPALITIES,
    ActionInput,
    BeneficiaryInput,
    Professional,
    Summary,
)
from app.domain.rules import can_transition
from app.infrastructure.models import Action, Audit, Beneficiary, Outbox, Participation


def audit(session: Session, professional: Professional, operation: str, entity_id: str) -> None:
    session.add(
        Audit(
            profissional_id=professional.profissional_id, operacao=operation, entidade_id=entity_id
        )
    )


def action_or_404(session: Session, identifier: str) -> Action:
    row = session.get(Action, identifier)
    if not row:
        raise HTTPException(404, "Ação não encontrada.")
    return row


def require_version(row: Action, version: int) -> None:
    if row.versao != version:
        raise HTTPException(409, "Esta ação foi alterada. Recarregue antes de salvar.")


def snapshot(session: Session, row: Action) -> dict:
    count = session.scalar(
        select(func.count()).select_from(Participation).where(Participation.acao_id == row.id)
    )
    delivery = session.scalar(
        select(Outbox).where(Outbox.idempotency_key == f"acao:{row.id}:v{row.versao}")
    )
    return {
        "id": row.id,
        "versao": row.versao,
        "nome": row.nome,
        "categoria": row.categoria,
        "descricao": row.descricao,
        "resumo_publico": row.resumo_publico,
        "inicio_em": row.inicio_em,
        "fim_em": row.fim_em,
        "status": row.status,
        "locais": [
            {**p, "municipio_nome": MUNICIPALITIES[p["municipio_ibge"]]} for p in row.locais
        ],
        "beneficiarios": count,
        "pessoas_contempladas": session.scalar(
            select(func.count(func.distinct(Participation.beneficiario_id))).where(
                Participation.acao_id == row.id
            )
        )
        or 0,
        "integracao": {
            "status": delivery.status,
            "enviado_em": delivery.enviado_em,
            "erro": delivery.erro,
        }
        if delivery
        else None,
        "criado_em": row.criado_em,
        "atualizado_em": row.atualizado_em,
        "aprovado_por": row.aprovado_por,
        "publicado_por": row.publicado_por,
    }


def enqueue(session: Session, row: Action) -> None:
    """Snapshot de substituição: consumidores não somam versões de uma mesma ação."""
    event_id = str(uuid4())
    count = (
        session.scalar(
            select(func.count()).select_from(Participation).where(Participation.acao_id == row.id)
        )
        or 0
    )
    summary = Summary(
        event_id=event_id,
        acao_id=row.id,
        revisao=row.versao,
        operacao="archive" if row.status == "arquivada" else "upsert",
        categoria=row.categoria,
        inicio_em=row.inicio_em,
        fim_em=row.fim_em,
        municipios_ibge=sorted({p["municipio_ibge"] for p in row.locais}),
        quantidade_acoes=0 if row.status == "arquivada" else 1,
        quantidade_participacoes=0 if row.status == "arquivada" else count,
        quantidade_pessoas_contempladas=0
        if row.status == "arquivada"
        else (
            session.scalar(
                select(func.count(func.distinct(Participation.beneficiario_id))).where(
                    Participation.acao_id == row.id
                )
            )
            or 0
        ),
        publicavel=row.status == "publicada",
    )
    session.add(
        Outbox(
            id=event_id,
            idempotency_key=f"acao:{row.id}:v{row.versao}",
            payload=summary.model_dump(mode="json"),
        )
    )


def save_action(
    session: Session, data: ActionInput, professional: Professional, identifier: str | None = None
) -> dict:
    values = data.model_dump(mode="json", exclude={"versao"})
    if identifier:
        row = action_or_404(session, identifier)
        require_version(row, data.versao)
        if row.status == "arquivada":
            raise HTTPException(409, "Ação arquivada não pode ser editada.")
        if row.locais != values["locais"] and session.scalar(
            select(func.count())
            .select_from(Participation)
            .where(
                Participation.acao_id == row.id,
                Participation.local_indice.is_not(None),
            )
        ):
            raise HTTPException(
                409,
                "Há participações vinculadas aos locais. Preserve os locais até revisar os vínculos.",
            )
        # CAS impede perda de alterações entre operadores.
        from sqlalchemy import update

        changed = session.execute(
            update(Action)
            .where(Action.id == identifier, Action.versao == data.versao)
            .values(
                **values,
                versao=data.versao + 1,
                status="em_revisao",
                aprovado_por=None,
                publicado_por=None,
                atualizado_em=datetime.now(UTC),
            )
        )
        if changed.rowcount != 1:
            raise HTTPException(409, "Esta ação foi alterada. Recarregue antes de salvar.")
        session.expire_all()
        row = session.get(Action, identifier)
    else:
        if data.versao != 0:
            raise HTTPException(422, "A versão inicial deve ser zero.")
        row = Action(**values, criado_por=professional.profissional_id)
        session.add(row)
        session.flush()
    audit(session, professional, "acoes.update" if identifier else "acoes.create", row.id)
    enqueue(session, row)
    return snapshot(session, row)


def change_status(
    session: Session, identifier: str, version: int, target: str, professional: Professional
) -> dict:
    row = action_or_404(session, identifier)
    require_version(row, version)
    if not can_transition(row.status, target):
        raise HTTPException(409, "Transição de status não permitida.")
    if target in {"validada", "publicada"} and not row.resumo_publico.strip():
        raise HTTPException(422, "Revise e preencha o resumo público antes da aprovação.")
    from sqlalchemy import update

    values = {"status": target, "versao": version + 1, "atualizado_em": datetime.now(UTC)}
    if target == "validada":
        values["aprovado_por"] = professional.profissional_id
    if target == "em_revisao":
        values["aprovado_por"] = values["publicado_por"] = None
    if target == "publicada":
        values["publicado_por"] = professional.profissional_id
    result = session.execute(
        update(Action).where(Action.id == identifier, Action.versao == version).values(**values)
    )
    if result.rowcount != 1:
        raise HTTPException(409, "Esta ação foi alterada. Recarregue antes de continuar.")
    session.expire_all()
    row = session.get(Action, identifier)
    audit(session, professional, "acoes." + target, row.id)
    enqueue(session, row)
    return snapshot(session, row)


def cipher() -> Fernet:
    key = get_settings().beneficiaries_key.get_secret_value()
    if not key:
        raise HTTPException(503, "Configuração de proteção dos beneficiários pendente.")
    return Fernet(key.encode())


def add_beneficiary(
    session: Session,
    identifier: str,
    data: BeneficiaryInput,
    professional: Professional,
    source: str | None = None,
) -> str:
    action = action_or_404(session, identifier)
    if action.status == "arquivada":
        raise HTTPException(409, "Ação arquivada não recebe participações.")
    if data.local_indice is not None and data.local_indice >= len(action.locais):
        raise HTTPException(422, "Local não pertence à ação.")
    if source:
        previous = session.scalar(select(Participation).where(Participation.origem == source))
        if previous:
            person = session.get(Beneficiary, previous.beneficiario_id)
            stored = json.loads(cipher().decrypt(person.dados_cifrados.encode()))
            if (
                previous.acao_id != identifier
                or stored != {"id": person.id, "nome": data.nome}
                or person.municipio_residencia_ibge != data.municipio_residencia_ibge
                or previous.local_indice != data.local_indice
            ):
                raise HTTPException(
                    409, "Origem já importada com outros dados. Solicite correção supervisionada."
                )
            return "existente"
    beneficiary_id = str(uuid4())
    encrypted = (
        cipher()
        .encrypt(json.dumps({"id": beneficiary_id, "nome": data.nome}, ensure_ascii=False).encode())
        .decode()
    )
    session.add(
        Beneficiary(
            id=beneficiary_id,
            dados_cifrados=encrypted,
            municipio_residencia_ibge=data.municipio_residencia_ibge,
        )
    )
    session.flush()
    session.add(
        Participation(
            acao_id=identifier,
            beneficiario_id=beneficiary_id,
            local_indice=data.local_indice,
            origem=source,
        )
    )
    audit(session, professional, "beneficiarios.create", beneficiary_id)
    return "incluido"


class SqlActionsRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, data: ActionInput, professional: Professional, identifier: str | None = None
    ) -> dict:
        return save_action(self.session, data, professional, identifier)

    def transition(
        self, identifier: str, version: int, target: str, professional: Professional
    ) -> dict:
        return change_status(self.session, identifier, version, target, professional)
