"""Encrypted, ID-bound registration envelope; legacy name-only records remain readable."""

import json

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from app.domain.contracts import BeneficiaryData
from app.infrastructure.models import Beneficiary


def decode_beneficiary(person: Beneficiary, encryption: Fernet) -> tuple[BeneficiaryData, int]:
    try:
        raw = json.loads(encryption.decrypt(person.dados_cifrados.encode()))
        if not isinstance(raw, dict) or raw.pop("id", None) != person.id:
            raise ValueError("ID mismatch")
        version = raw.pop("versao", 1)
        if type(version) is not int or version < 1:
            raise ValueError("Invalid version")
        if "municipio_residencia_ibge" in raw and (
            raw["municipio_residencia_ibge"] != person.municipio_residencia_ibge
        ):
            raise ValueError("Municipality mismatch")
        raw["municipio_residencia_ibge"] = person.municipio_residencia_ibge
        return BeneficiaryData.model_validate(raw), version
    except (ValueError, TypeError, KeyError, InvalidToken):
        raise HTTPException(503, "Falha na integridade do cadastro do beneficiário.") from None


def encode_beneficiary(
    identifier: str, data: BeneficiaryData, version: int, encryption: Fernet
) -> str:
    values = BeneficiaryData.model_validate(
        data.model_dump(include=set(BeneficiaryData.model_fields))
    )
    return encryption.encrypt(
        json.dumps(
            {
                "id": identifier,
                "versao": version,
                **values.model_dump(mode="json", exclude_none=True),
            },
            ensure_ascii=False,
        ).encode()
    ).decode()


def same_beneficiary(person: Beneficiary, data: BeneficiaryData, encryption: Fernet) -> bool:
    stored, _ = decode_beneficiary(person, encryption)
    requested = BeneficiaryData.model_validate(
        data.model_dump(include=set(BeneficiaryData.model_fields))
    )
    return stored == requested
