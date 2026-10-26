from datetime import datetime
from typing import Literal, Protocol

from pydantic import Field, SecretStr, field_validator

from app.domain.contracts import Professional, StrictModel, Summary

SCOPE = "acoes.resumos.read"


class CredentialMetadata(StrictModel):
    id: str
    nome: str
    token_mascarado: str
    escopo: Literal["acoes.resumos.read"]
    criado_em: datetime
    expira_em: datetime
    revogado_em: datetime | None
    ultimo_uso_em: datetime | None
    chamadas: int
    status: Literal["ativa", "expirada", "revogada"]


class IssuedCredential(StrictModel):
    credencial: CredentialMetadata
    token: str


class ServiceHealth(StrictModel):
    status: Literal["API_OK"]
    schema_version: Literal["1.1"]
    limite_por_minuto: Literal[60]


class ExportPage(StrictModel):
    schema_version: Literal["1.1"]
    source: Literal["ac-actions-map"]
    exportacao_id: str
    capturado_em: datetime
    expira_em: datetime
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    page: int = Field(ge=1, le=10)
    page_size: Literal[100]
    total_pages: int = Field(ge=1, le=10)
    total_itens: int = Field(ge=0, le=1000)
    quantidade_acoes: int = Field(ge=0)
    quantidade_pessoas_contempladas: int = Field(ge=0)
    escopo: str
    items: list[Summary]


class CredentialAuthorization(StrictModel):
    password: SecretStr = Field(min_length=1, max_length=1024)


class CredentialInput(CredentialAuthorization):
    nome: str = Field(min_length=3, max_length=80)
    validade_dias: int = Field(default=90, ge=1, le=365, strict=True)

    @field_validator("nome")
    @classmethod
    def safe_name(cls, value: str) -> str:
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("Informe um nome sem caracteres de controle.")
        return value


class CredentialRepository(Protocol):
    def create(self, data: CredentialInput, professional: Professional) -> dict: ...
    def revoke(self, identifier: str, professional: Professional) -> dict: ...
    def rotate(
        self, identifier: str, data: CredentialInput, professional: Professional
    ) -> dict: ...
