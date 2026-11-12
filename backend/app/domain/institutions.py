"""Instituições reutilizáveis; papel e autorização pertencem a cada ação."""

from typing import Literal, Self

from pydantic import Field, model_validator

from app.domain.base import StrictModel

InstitutionType = Literal["ORGAO_GOVERNAMENTAL", "CLINICA", "ORGANIZACAO_EMPRESA", "OUTRO"]


class InstitutionInput(StrictModel):
    nome: str = Field(min_length=2, max_length=160)
    tipo: InstitutionType
    aliases: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def aliases_valid(self) -> Self:
        if any(not value.strip() or len(value) > 160 for value in self.aliases):
            raise ValueError("Aliases devem ter de 1 a 160 caracteres.")
        return self
