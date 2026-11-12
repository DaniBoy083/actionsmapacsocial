"""Campos literais do XLSX de origem; unidades/faixas não são inferidas pelo software."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.domain.base import StrictModel


class EyeFields(StrictModel):
    esferico: str | None = Field(default=None, max_length=40)
    cilindrico: str | None = Field(default=None, max_length=40)
    eixo: str | None = Field(default=None, max_length=40)
    dp: str | None = Field(default=None, max_length=40)

    @field_validator("*", mode="before")
    @classmethod
    def blank(cls, value):
        return value.strip() or None if isinstance(value, str) else value


class ClinicalFields(StrictModel):
    glicose: str | None = Field(default=None, max_length=80)
    pressao: str | None = Field(default=None, max_length=80)
    tipo_sangue: str | None = Field(default=None, max_length=32)
    od: EyeFields = Field(default_factory=EyeFields)
    oe: EyeFields = Field(default_factory=EyeFields)
    adicao: str | None = Field(default=None, max_length=40)
    lentes: str | None = Field(default=None, max_length=160)

    @field_validator("glicose", "pressao", "tipo_sangue", "adicao", "lentes", mode="before")
    @classmethod
    def blank(cls, value):
        return value.strip() or None if isinstance(value, str) else value


class ClinicalInput(StrictModel):
    versao: int = Field(default=0, ge=0, strict=True)
    campos: ClinicalFields


class ClinicalDesignationInput(StrictModel):
    profissional_id: UUID
    versao: int = Field(default=0, ge=0, strict=True)
    ativo: bool = Field(default=True, strict=True)


class ClinicalView(ClinicalInput):
    id: str | None
    estado: Literal["EM_PREENCHIMENTO"] = "EM_PREENCHIMENTO"
    contexto: dict
    atualizado_em: datetime | None
