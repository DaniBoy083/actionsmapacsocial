"""Cadastro administrativo de profissionais; não constitui conta ou permissão clínica."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.domain.base import StrictModel

UF = Literal[
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
]


class StaffData(StrictModel):
    nome: str = Field(min_length=2, max_length=160)
    categoria: Literal["MEDICO", "OPTOMETRISTA", "RECEPCAO"]
    identidade_institucional_id: str | None = Field(default=None, min_length=1, max_length=160)
    registro_conselho: str | None = Field(default=None, max_length=40)
    registro_numero: str | None = Field(default=None, max_length=40)
    registro_uf: UF | None = None
    rqe: str | None = Field(default=None, max_length=40)
    habilitacao_validada: bool = Field(default=False, strict=True)
    habilitacao_referencia: str = Field(default="", max_length=200)
    registro_clinico_autorizado: bool = Field(default=False, strict=True)
    autorizacao_clinica_referencia: str = Field(default="", max_length=200)
    ativo: bool = Field(default=True, strict=True)
    divulgacao_autorizada: bool = Field(default=False, strict=True)
    divulgacao_referencia: str = Field(default="", max_length=200)

    @field_validator("registro_conselho", "registro_numero", "registro_uf", "rqe", mode="before")
    @classmethod
    def optional_registration(cls, value):
        return value.strip().upper() or None if isinstance(value, str) else value

    @model_validator(mode="after")
    def consistent(self) -> Self:
        registration = (self.registro_conselho, self.registro_numero, self.registro_uf)
        if any(registration) and not all(registration):
            raise ValueError("Informe conselho, número e UF juntos ou deixe o registro em branco.")
        if self.categoria == "MEDICO" and (
            not all(registration) or self.registro_conselho != "CRM"
        ):
            raise ValueError("Cadastro médico exige CRM, número e UF.")
        if self.categoria != "MEDICO" and (self.registro_conselho == "CRM" or self.rqe):
            raise ValueError("CRM e RQE são campos exclusivos do cadastro médico.")
        if self.categoria == "RECEPCAO" and (
            any(registration) or self.habilitacao_validada or self.habilitacao_referencia
        ):
            raise ValueError("Recepção não recebe habilitação ou registro clínico.")
        if self.habilitacao_validada and (not all(registration) or not self.habilitacao_referencia):
            raise ValueError("Registre o conselho e a referência da conferência de habilitação.")
        if self.registro_clinico_autorizado and not (
            self.categoria != "RECEPCAO"
            and self.habilitacao_validada
            and self.autorizacao_clinica_referencia
        ):
            raise ValueError(
                "Registro clínico exige habilitação e autorização específica registrada."
            )
        if self.categoria == "RECEPCAO" and self.autorizacao_clinica_referencia:
            raise ValueError("Recepção não recebe autorização clínica.")
        if self.divulgacao_autorizada and not (
            self.categoria == "MEDICO"
            and self.ativo
            and self.habilitacao_validada
            and self.divulgacao_referencia
        ):
            raise ValueError(
                "Divulgação médica exige cadastro ativo, conferência e autorização registrada."
            )
        return self


class StaffInput(StaffData):
    versao: int = Field(default=0, ge=0, strict=True)


class StaffView(StaffData):
    id: str
    versao: int
    atualizado_em: datetime
    conferido_por: str | None
    conferido_em: datetime | None
    divulgacao_registrada_por: str | None
    divulgacao_registrada_em: datetime | None


class AssignmentScope(StrictModel):
    acao_versao: int = Field(ge=1, strict=True)
    profissional_versao: int = Field(ge=1, strict=True)
    locais_indices: list[int] | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("locais_indices", mode="before")
    @classmethod
    def valid_indices(cls, value):
        if value is not None and (
            not isinstance(value, list)
            or any(type(index) is not int or index < 0 for index in value)
            or len(value) != len(set(value))
        ):
            raise ValueError("Selecione locais distintos da ação.")
        return sorted(value) if value is not None else None


class AssignmentInput(AssignmentScope):
    profissional_id: UUID


class AssignmentUpdate(AssignmentScope):
    versao: int = Field(ge=1, strict=True)
    ativo: bool = Field(strict=True)


class AssignmentView(StrictModel):
    id: str
    versao: int
    acao_id: str
    profissional_id: str
    profissional: StaffView
    papel: Literal["PROFISSIONAL", "RECEPCAO"]
    ativo: bool
    locais_indices: list[int] | None
    locais_snapshot: list[dict] | None
    profissional_snapshot: dict
    atualizado_em: datetime


class StaffPage(StrictModel):
    items: list[StaffView]
    total: int
    pagina: int
    tamanho: int


class AssignmentPage(StrictModel):
    items: list[AssignmentView]
    total: int
    pagina: int
    tamanho: int
