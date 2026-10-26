import hashlib
import json
import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import String, case, cast, delete, func, literal, select, text, update
from sqlalchemy.orm import Session

from app.domain.contracts import Professional, Summary
from app.domain.integrations import SCOPE, CredentialInput
from app.infrastructure.actions import audit
from app.infrastructure.models import (
    Action,
    Audit,
    IntegrationCredential,
    IntegrationExport,
    Outbox,
)

RATE_LIMIT = 60
EXPORT_SECONDS = 300
MAX_EXPORT_ITEMS = 1000


def metadata(row: IntegrationCredential) -> dict:
    now = datetime.now(UTC)
    return {
        "id": row.id,
        "nome": row.nome,
        "token_mascarado": row.prefixo + "…" + row.sufixo,
        "escopo": row.escopo,
        "criado_em": row.criado_em,
        "expira_em": row.expira_em,
        "revogado_em": row.revogado_em,
        "ultimo_uso_em": row.ultimo_uso_em,
        "chamadas": row.chamadas,
        "status": "revogada"
        if row.revogado_em
        else (
            "expirada" if row.expira_em and row.expira_em.replace(tzinfo=UTC) <= now else "ativa"
        ),
    }


def credential_lock(session: Session) -> None:
    if session.get_bind().dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_xact_lock(hashtext('actions_map.credentials'))"))


class SqlCredentialRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: CredentialInput, professional: Professional) -> dict:
        credential_lock(self.session)
        active = self.session.scalar(
            select(func.count())
            .select_from(IntegrationCredential)
            .where(
                IntegrationCredential.revogado_em.is_(None),
                IntegrationCredential.expira_em.is_(None)
                | (IntegrationCredential.expira_em > datetime.now(UTC)),
            )
        )
        if active >= 20:
            raise HTTPException(
                409, "Limite de 20 tokens ativos. Revogue um token antes de criar outro."
            )
        identifier = str(uuid4())
        token = "acm_" + identifier.replace("-", "") + "_" + secrets.token_urlsafe(32)
        row = IntegrationCredential(
            id=identifier,
            nome=data.nome,
            prefixo=token[:16],
            sufixo=token[-4:],
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            escopo=SCOPE,
            criado_por=professional.profissional_id,
            expira_em=datetime.now(UTC) + timedelta(days=data.validade_dias)
            if data.validade_dias is not None
            else None,
        )
        self.session.add(row)
        self.session.flush()
        audit(self.session, professional, "integracoes.token.create", row.id)
        return {"credencial": metadata(row), "token": token}

    def revoke(self, identifier: str, professional: Professional) -> dict:
        credential_lock(self.session)
        row = self.session.get(IntegrationCredential, identifier)
        if not row:
            raise HTTPException(404, "Token não encontrado.")
        if not row.revogado_em:
            row.revogado_em = datetime.now(UTC)
            self.session.execute(
                delete(IntegrationExport).where(
                    IntegrationExport.credencial_id == row.id,
                )
            )
            audit(self.session, professional, "integracoes.token.revoke", row.id)
        return metadata(row)

    def rotate(self, identifier: str, data: CredentialInput, professional: Professional) -> dict:
        # Revogação e substituição pertencem à mesma transação: falha não perde a credencial antiga.
        credential_lock(self.session)
        row = self.session.get(IntegrationCredential, identifier)
        if not row:
            raise HTTPException(404, "Token não encontrado.")
        if row.revogado_em or (
            row.expira_em and row.expira_em.replace(tzinfo=UTC) <= datetime.now(UTC)
        ):
            raise HTTPException(409, "Crie um novo token para substituir uma credencial inativa.")
        self.revoke(identifier, professional)
        self.session.flush()
        result = self.create(data, professional)
        audit(self.session, professional, "integracoes.token.rotate", identifier)
        return result


def consume_service_token(session: Session, authorization: str) -> tuple[str, int]:
    match = re.fullmatch(r"Bearer (acm_[a-f0-9]{32}_[A-Za-z0-9_-]{43})", authorization)
    if not match:
        return "", 401
    token_hash = hashlib.sha256(match[1].encode()).hexdigest()
    now = datetime.now(UTC)
    minute = int(now.timestamp() // 60)
    row = session.scalar(
        select(IntegrationCredential)
        .where(
            IntegrationCredential.token_hash == token_hash,
            IntegrationCredential.escopo == SCOPE,
            IntegrationCredential.revogado_em.is_(None),
            IntegrationCredential.expira_em.is_(None) | (IntegrationCredential.expira_em > now),
        )
        .with_for_update()
    )
    if not row:
        return "", 401
    # UPDATE condicional mantém a cota e a revogação válidas entre instâncias.
    used = session.scalar(
        update(IntegrationCredential)
        .where(
            IntegrationCredential.id == row.id,
            IntegrationCredential.revogado_em.is_(None),
            IntegrationCredential.expira_em.is_(None) | (IntegrationCredential.expira_em > now),
            (IntegrationCredential.janela_minuto != minute)
            | (IntegrationCredential.chamadas_janela < RATE_LIMIT),
        )
        .values(
            chamadas=IntegrationCredential.chamadas + 1,
            ultimo_uso_em=now,
            janela_minuto=minute,
            chamadas_janela=case(
                (
                    IntegrationCredential.janela_minuto == minute,
                    IntegrationCredential.chamadas_janela + 1,
                ),
                else_=1,
            ),
        )
        .execution_options(synchronize_session=False)
        .returning(IntegrationCredential.id)
    )
    return (used, 200) if used else ("", 429)


def export_page(session: Session, credential_id: str, page: int, identifier: str | None) -> dict:
    now = datetime.now(UTC)
    session.execute(delete(IntegrationExport).where(IntegrationExport.expira_em <= now))
    if identifier:
        row = session.scalar(
            select(IntegrationExport).where(
                IntegrationExport.id == identifier,
                IntegrationExport.credencial_id == credential_id,
            )
        )
        if not row or row.expira_em.replace(tzinfo=UTC) <= now:
            raise HTTPException(
                410, "Exportação indisponível ou expirada. Reinicie pela primeira página."
            )
    else:
        if page != 1:
            raise HTTPException(422, "Informe exportacao_id para consultar outras páginas.")
        session.scalar(
            select(IntegrationCredential.id)
            .where(
                IntegrationCredential.id == credential_id,
            )
            .with_for_update()
        )
        active = session.scalar(
            select(func.count())
            .select_from(IntegrationExport)
            .where(
                IntegrationExport.credencial_id == credential_id,
            )
        )
        if active >= 5:
            raise HTTPException(
                429,
                "Reutilize a exportação atual ou aguarde cinco minutos.",
                headers={"Retry-After": "300"},
            )
        # Uma consulta lê revisão e evento no mesmo snapshot; nenhuma ficha/identidade entra na projeção.
        values = session.execute(
            select(Action.id, Outbox.payload)
            .outerjoin(
                Outbox,
                Outbox.idempotency_key
                == literal("acao:") + Action.id + literal(":v") + cast(Action.versao, String),
            )
            .order_by(Action.id)
            .limit(MAX_EXPORT_ITEMS + 1)
        ).all()
        if len(values) > MAX_EXPORT_ITEMS:
            raise HTTPException(
                503, "Limite de exportação atingido. Procure a equipe de Tecnologia."
            )
        if any(not payload or payload.get("schema_version") != "1.1" for _, payload in values):
            raise HTTPException(503, "Há ações que precisam de nova revisão antes da exportação.")
        items = [Summary.model_validate(payload).model_dump(mode="json") for _, payload in values]
        serialized = json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(serialized.encode()) > 2 * 1024 * 1024:
            raise HTTPException(503, "Exportação excede o limite. Procure a equipe de Tecnologia.")
        row = IntegrationExport(
            credencial_id=credential_id,
            criado_em=now,
            expira_em=now + timedelta(seconds=EXPORT_SECONDS),
            payload={"items": items, "checksum": hashlib.sha256(serialized.encode()).hexdigest()},
        )
        session.add(row)
        session.flush()
        session.add(
            Audit(
                profissional_id="service:" + credential_id,
                operacao="integracoes.export.create",
                entidade_id=row.id,
            )
        )
    items = row.payload["items"]
    total_pages = max(1, (len(items) + 99) // 100)
    if page > total_pages:
        raise HTTPException(422, "Página fora da exportação.")
    return {
        "schema_version": "1.1",
        "source": "ac-actions-map",
        "exportacao_id": row.id,
        "capturado_em": row.criado_em.replace(tzinfo=UTC),
        "expira_em": row.expira_em.replace(tzinfo=UTC),
        "checksum": row.payload["checksum"],
        "page": page,
        "page_size": 100,
        "total_pages": total_pages,
        "total_itens": len(items),
        "quantidade_acoes": sum(item["quantidade_acoes"] for item in items if item["publicavel"]),
        "quantidade_pessoas_contempladas": sum(
            item["quantidade_pessoas_contempladas"] for item in items if item["publicavel"]
        ),
        "escopo": "Revisões correntes e retiradas; totais de ações publicadas; sem dados individuais.",
        "items": items[(page - 1) * 100 : page * 100],
    }
