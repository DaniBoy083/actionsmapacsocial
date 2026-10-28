import json
import re
import unicodedata
from datetime import date, datetime
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


class BeneficiaryData(StrictModel):
    nome: str = Field(min_length=2, max_length=160)
    telefone: str | None = Field(default=None, max_length=24)
    cpf: str | None = Field(default=None, max_length=14)
    cpf_documento: str | None = Field(default=None, max_length=14)
    data_nascimento: date | None = None
    data_ficha: date | None = None
    municipio_ficha_ibge: str | None = None
    responsavel: str | None = Field(default=None, max_length=160)
    observacoes: str | None = Field(default=None, max_length=1000)
    recebimento_confirmado: bool | None = Field(default=None, strict=True)
    municipio_residencia_ibge: str | None = None

    @field_validator("municipio_residencia_ibge", "municipio_ficha_ibge")
    @classmethod
    def municipality(cls, value: str | None) -> str | None:
        return Location.municipality(value) if value else None

    @field_validator("responsavel", "observacoes", mode="before")
    @classmethod
    def optional_text(cls, value):
        return value.strip() or None if isinstance(value, str) else value

    @field_validator("cpf")
    @classmethod
    def valid_cpf(cls, value: str | None) -> str | None:
        if not value:
            return None
        if not re.fullmatch(r"[0-9.\- ]+", value):
            raise ValueError("Informe um CPF válido ou deixe o campo em branco.")
        digits = re.sub(r"\D", "", value)
        if len(digits) != 11 or len(set(digits)) == 1:
            raise ValueError("Informe um CPF válido ou deixe o campo em branco.")
        for size in (9, 10):
            check = sum(int(digits[i]) * (size + 1 - i) for i in range(size)) * 10 % 11 % 10
            if check != int(digits[size]):
                raise ValueError("Informe um CPF válido ou deixe o campo em branco.")
        return digits

    @field_validator("cpf_documento")
    @classmethod
    def documentary_cpf(cls, value: str | None) -> str | None:
        if not value:
            return None
        if not re.fullmatch(r"[0-9.\- ]+", value) or len(re.sub(r"\D", "", value)) != 11:
            raise ValueError("Transcreva os 11 dígitos legíveis do documento ou deixe em branco.")
        return re.sub(r"\D", "", value)

    @field_validator("telefone")
    @classmethod
    def valid_phone(cls, value: str | None) -> str | None:
        if not value:
            return None
        if not re.fullmatch(r"[+0-9() .\-]+", value):
            raise ValueError("Transcreva o telefone informado, sem inventar DDD.")
        digits = re.sub(r"\D", "", value)
        if len(digits) in {12, 13} and digits.startswith("55"):
            digits = digits[2:]
        if not 7 <= len(digits) <= 13:
            raise ValueError("Transcreva o telefone informado, sem inventar DDD.")
        return digits

    @field_validator("data_nascimento")
    @classmethod
    def valid_birth(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("A data de nascimento não pode estar no futuro.")
        return value

    @model_validator(mode="after")
    def dates_consistent(self) -> Self:
        if self.data_nascimento and self.data_ficha and self.data_nascimento > self.data_ficha:
            raise ValueError("A data da ficha não pode ser anterior ao nascimento.")
        return self


class BeneficiaryInput(BeneficiaryData):
    local_indice: int | None = Field(default=None, ge=0)


class BeneficiaryUpdate(BeneficiaryInput):
    versao: int = Field(ge=1, strict=True)


class BeneficiaryAction(StrictModel):
    id: str
    nome: str


class BeneficiarySheet(BeneficiaryUpdate):
    id: str
    acao: BeneficiaryAction
    municipio_ficha_nome: str | None
    municipio_residencia_nome: str | None
    segunda_via: bool
    emitido_em: datetime | None


class ImportRecord(BeneficiaryInput):
    pagina: int = Field(ge=1, le=200)
    revisado: bool


class ImportConfirmation(StrictModel):
    importacao_id: str
    acao_id: str
    registros: list[ImportRecord] = Field(min_length=1, max_length=200)
    confirmacao_producao: bool = False

    @model_validator(mode="after")
    def reviewed(self) -> Self:
        if not all(row.revisado for row in self.registros):
            raise ValueError("Revise todos os registros antes de confirmar.")
        if len({row.pagina for row in self.registros}) != len(self.registros):
            raise ValueError("Há páginas repetidas no lote.")
        return self


class Summary(StrictModel):
    schema_version: Literal["1.1"] = "1.1"
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
    quantidade_pessoas_contempladas: int = Field(ge=0)
    publicavel: bool = False

    @field_validator("municipios_ibge")
    @classmethod
    def valid_municipalities(cls, values: list[str]) -> list[str]:
        if not values or len(set(values)) != len(values):
            raise ValueError("Informe municípios válidos sem repetição.")
        return sorted(Location.municipality(value) for value in values)
