import json
import unicodedata
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

MUNICIPALITIES: dict[str, str] = json.loads(
    Path(__file__).with_name("paraiba_municipalities.json").read_text(encoding="utf-8")
)


def normalize(value: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value.strip().lower())
        if unicodedata.category(c) != "Mn"
    )


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(StrictModel):
    identifier: str = Field(min_length=1, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=1024)


class Professional(StrictModel):
    profissional_id: str
    nome: str
    tipo_login: str
    equipe: str
    ativo: bool = True

    @property
    def allowed(self) -> bool:
        return (
            self.ativo
            and self.tipo_login == "administracao"
            and self.equipe in {"administracao", "tecnologia"}
        )


class Status(StrEnum):
    DRAFT = "rascunho"
    REVIEW = "em_revisao"
    VALIDATED = "validada"
    PUBLISHED = "publicada"
    ARCHIVED = "arquivada"


class Location(StrictModel):
    municipio_ibge: str
    nome_local: str = Field(default="", max_length=160)

    @field_validator("municipio_ibge")
    @classmethod
    def municipality(cls, value: str) -> str:
        if value not in MUNICIPALITIES:
            raise ValueError("Selecione um município válido da Paraíba.")
        return value


class ActionInput(StrictModel):
    nome: str = Field(min_length=2, max_length=160)
    categoria: str = Field(default="", max_length=80)
    descricao: str = Field(default="", max_length=4000)
    resumo_publico: str = Field(default="", max_length=1000)
    inicio_em: date | None = None
    fim_em: date | None = None
    locais: list[Location] = Field(min_length=1, max_length=100)
    versao: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.fim_em and not self.inicio_em:
            raise ValueError("Informe a data inicial antes da data final.")
        if self.inicio_em and self.fim_em and self.fim_em < self.inicio_em:
            raise ValueError("A data final deve ser igual ou posterior à inicial.")
        keys = [(p.municipio_ibge, normalize(p.nome_local)) for p in self.locais]
        if len(set(keys)) != len(keys):
            raise ValueError("Remova o local repetido.")
        return self


class Version(StrictModel):
    versao: int = Field(ge=1)


class BeneficiaryInput(StrictModel):
    nome: str = Field(min_length=2, max_length=160)
    municipio_residencia_ibge: str | None = None
    local_indice: int | None = Field(default=None, ge=0)

    @field_validator("municipio_residencia_ibge")
    @classmethod
    def municipality(cls, value: str | None) -> str | None:
        return Location.municipality(value) if value else None


class ImportRecord(BeneficiaryInput):
    pagina: int = Field(ge=1, le=200)
    revisado: bool


class ImportConfirmation(StrictModel):
    importacao_id: str
    acao_id: str
    registros: list[ImportRecord] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def reviewed(self) -> Self:
        if not all(row.revisado for row in self.registros):
            raise ValueError("Revise todos os registros antes de confirmar.")
        if len({row.pagina for row in self.registros}) != len(self.registros):
            raise ValueError("Há páginas repetidas no lote.")
        return self


class Summary(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    event_id: str
    source: Literal["ac-actions-map"] = "ac-actions-map"
    acao_id: str
    revisao: int = Field(ge=1)
    operacao: Literal["upsert", "archive"] = "upsert"
    categoria: str
    inicio_em: date | None
    fim_em: date | None
    municipios_ibge: list[str]
    quantidade_acoes: int = Field(ge=0, le=1)
    quantidade_participacoes: int = Field(ge=0)
    publicavel: bool = False
