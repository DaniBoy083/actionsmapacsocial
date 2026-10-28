"""Reviewed completion by exact source/page. Never replaces existing values."""

import hashlib
from collections import Counter
from typing import Literal

from pydantic import Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.contracts import BeneficiaryData, BeneficiaryUpdate, Professional, StrictModel
from app.infrastructure.actions import cipher
from app.infrastructure.beneficiaries import SqlBeneficiariesRepository
from app.infrastructure.beneficiary_data import decode_beneficiary
from app.infrastructure.models import Beneficiary, Participation

COMPLETION_FIELDS = set(BeneficiaryData.model_fields) - {"nome", "municipio_residencia_ibge"}


class CompletionRecord(StrictModel):
    pagina: int = Field(ge=1, le=200)
    campos: dict[str, str | bool]
    revisado: Literal[True]

    @field_validator("campos")
    @classmethod
    def approved_fields(cls, value):
        if not value or not set(value) <= COMPLETION_FIELDS:
            raise ValueError("Campos de complemento inválidos.")
        BeneficiaryData.model_validate({"nome": "Validação de campos", **value})
        return value


class CompletionManifest(StrictModel):
    hash_arquivo: str = Field(pattern=r"^[a-f0-9]{64}$")
    acao_id: str
    paginas: int = Field(ge=1, le=200)
    registros: list[CompletionRecord] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def pages_consistent(self):
        pages = [record.pagina for record in self.registros]
        if len(set(pages)) != len(pages) or any(page > self.paginas for page in pages):
            raise ValueError("Páginas inconsistentes no complemento.")
        return self


def complete_missing(
    session: Session, manifest: CompletionManifest, professional: Professional
) -> dict:
    if not professional.allowed:
        raise PermissionError("Operador sem autorização.")
    repository = SqlBeneficiariesRepository(session)
    changed = 0
    fields_changed = Counter()
    conflicts = []
    # Preflight the entire manifest before any write or audit.
    plan = []
    for record in manifest.registros:
        source = hashlib.sha256(
            f"{manifest.hash_arquivo}:{record.pagina}:{manifest.acao_id}".encode()
        ).hexdigest()
        found = session.execute(
            select(Beneficiary, Participation)
            .join(Participation)
            .where(
                Participation.acao_id == manifest.acao_id,
                Participation.origem == source,
            )
        ).one_or_none()
        if not found:
            raise ValueError("Origem de uma página não encontrada; lote interrompido.")
        person, participation = found
        stored, version = decode_beneficiary(person, cipher())
        incoming = BeneficiaryData.model_validate({"nome": stored.nome, **record.campos})
        values = stored.model_dump(mode="json")
        modified = []
        for key in record.campos:
            proposed = incoming.model_dump(mode="json")[key]
            if values[key] is None and proposed is not None:
                values[key] = proposed
                modified.append(key)
            elif values[key] != proposed:
                conflicts.append({"pagina": record.pagina, "campo": key})
        update = BeneficiaryUpdate(
            **values, versao=version, local_indice=participation.local_indice
        )
        plan.append((person.id, update, modified))
    for person_id, data, modified in plan:
        if modified:
            repository.update(manifest.acao_id, person_id, data, professional)
            changed += 1
            fields_changed.update(modified)
    return {
        "registros_conferidos": len(plan),
        "registros_atualizados": changed,
        "campos_preenchidos": dict(fields_changed),
        "conflitos_preservados": conflicts,
    }
