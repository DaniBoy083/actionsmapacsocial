"""Credenciais exclusivas do Actions Map; não são dados clínicos ou contas AC."""

from pydantic import Field, SecretStr, field_validator

from app.domain.base import StrictModel


class OperationalAccountInput(StrictModel):
    usuario: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9][a-z0-9._-]+$")
    nova_senha: SecretStr | None = Field(default=None, min_length=12, max_length=128)
    senha_institucional: SecretStr = Field(min_length=1, max_length=1024)
    ativo: bool = Field(default=True, strict=True)
    versao: int = Field(default=0, ge=0, strict=True)

    @field_validator("usuario", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class OperationalAccountView(StrictModel):
    usuario: str
    ativo: bool
    versao: int
