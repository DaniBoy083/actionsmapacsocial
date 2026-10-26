"""Adaptador operacional de carga local revisada, sem publicar o documento original."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Literal, Self
from uuid import NAMESPACE_URL, uuid5

from fastapi import HTTPException
from pydantic import Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.contracts import (
    ActionInput,
    BeneficiaryInput,
    ImportRecord,
    Professional,
    StrictModel,
    normalize,
)
from app.infrastructure.actions import add_beneficiary, audit, cipher, enqueue
from app.infrastructure.models import Action, Beneficiary, ImportBatch, Participation


class PendingPage(StrictModel):
    pagina: int = Field(ge=1, le=200)
    motivo: Literal["confirmar_grafia", "nome_ilegivel", "duplicidade", "nao_selecionada"]


class HistoricalManifest(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    hash_arquivo: str = Field(pattern=r"^[0-9a-f]{64}$")
    paginas: int = Field(ge=1, le=200)
    acao: ActionInput
    registros: list[ImportRecord] = Field(default_factory=list, max_length=200)
    pendencias: list[PendingPage] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def consistent(self) -> Self:
        pages = [row.pagina for row in self.registros + self.pendencias]
        if len(pages) != len(set(pages)) or set(pages) != set(range(1, self.paginas + 1)):
            raise ValueError("Cada página deve constar uma vez, como registro ou pendência.")
        if self.acao.versao != 0:
            raise ValueError("O manifesto descreve a criação inicial da ação.")
        if any(
            row.local_indice is not None and row.local_indice >= len(self.acao.locais)
            for row in self.registros
        ):
            raise ValueError("Local de participação não pertence à ação.")
        return self

    @property
    def action_id(self) -> str:
        return str(uuid5(NAMESPACE_URL, "ac-actions-map:historical-action:" + self.hash_arquivo))

    @property
    def batch_id(self) -> str:
        return str(uuid5(NAMESPACE_URL, "ac-actions-map:historical-batch:" + self.hash_arquivo))


def import_history(
    session: Session,
    manifest: HistoricalManifest,
    professional: Professional,
    *,
    action_only: bool = False,
) -> dict:
    """O chamador controla transação/backup e verifica arquivo, perfil e autorização.

    IDs derivados da fonte e proveniência por página impedem repetição da carga.
    Pendências nunca viram beneficiários; nomes não são usados para unir pessoas.
    """
    if not professional.allowed:
        raise PermissionError("Perfil não autorizado.")
    if not action_only and any(not row.revisado for row in manifest.registros):
        raise ValueError("Revise os nomes selecionados antes da gravação.")

    row = session.scalar(select(Action).where(Action.id == manifest.action_id).with_for_update())
    created = row is None
    if created:
        # Não criar uma segunda ação se alguém já a cadastrou manualmente.
        if any(
            normalize(name) == normalize(manifest.acao.nome)
            for name in session.scalars(select(Action.nome))
        ):
            raise ValueError("Já existe uma ação com este nome. Concilie o destino da carga.")
        row = Action(
            id=manifest.action_id,
            **manifest.acao.model_dump(mode="json", exclude={"versao"}),
            criado_por=professional.profissional_id,
        )
        session.add(row)
        session.flush()
        audit(session, professional, "acoes.create", row.id)
        enqueue(session, row)
    elif row.status == "arquivada":
        raise ValueError("Ação arquivada não recebe importação.")
    elif row.nome != manifest.acao.nome or row.locais != [
        item.model_dump() for item in manifest.acao.locais
    ]:
        raise ValueError("O cadastro foi alterado. Concilie a ação antes de continuar.")

    included = existing = 0
    if not action_only:
        batch = session.get(ImportBatch, manifest.batch_id)
        if not batch:
            batch = ImportBatch(
                id=manifest.batch_id,
                hash_arquivo=manifest.hash_arquivo,
                paginas=manifest.paginas,
                autor_id=professional.profissional_id,
            )
            session.add(batch)
        elif batch.hash_arquivo != manifest.hash_arquivo or batch.paginas != manifest.paginas:
            raise ValueError("A origem da importação não corresponde ao manifesto.")

        for record in manifest.registros:
            source = hashlib.sha256(
                f"{manifest.hash_arquivo}:{record.pagina}:{row.id}".encode()
            ).hexdigest()
            data = BeneficiaryInput(**record.model_dump(exclude={"pagina", "revisado"}))
            previous = session.execute(
                select(Beneficiary, Participation)
                .join(Participation)
                .where(Participation.origem == source)
            ).first()
            if previous:
                person, participation = previous
                stored = json.loads(cipher().decrypt(person.dados_cifrados.encode()))
                if (
                    stored != {"id": person.id, "nome": data.nome}
                    or person.municipio_residencia_ibge != data.municipio_residencia_ibge
                    or participation.local_indice != data.local_indice
                ):
                    raise HTTPException(
                        409,
                        "Página já importada com dados diferentes; solicite correção supervisionada.",
                    )
            result = add_beneficiary(session, row.id, data, professional, source)
            session.flush()
            included += result == "incluido"
            existing += result == "existente"
        if included:
            row.versao += 1
            row.atualizado_em = datetime.now(UTC)
            # Uma carga altera os indicadores e exige nova revisão editorial.
            row.status = "rascunho"
            row.aprovado_por = row.publicado_por = None
            session.flush()
            enqueue(session, row)
        audit(session, professional, "importacoes.confirmar", batch.id)

    return {
        "acao_id": row.id,
        "acao_criada": created,
        "incluidos": included,
        "existentes": existing,
        "pendentes": manifest.paginas if action_only else len(manifest.pendencias),
    }
