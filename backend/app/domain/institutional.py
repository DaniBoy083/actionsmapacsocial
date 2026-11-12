"""Metadados administrativos; não contêm campos da ficha clínica."""

from typing import Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.base import StrictModel


class Instrument(StrictModel):
    tipo: Literal["EMENDA", "CONVENIO", "OUTRO", "NAO_INFORMADO"] = "NAO_INFORMADO"
    nome: str = Field(default="", max_length=160)
    numero: str = Field(default="", max_length=80)
    autor: str = Field(default="", max_length=160)
    divulgacao_autorizada: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.tipo == "NAO_INFORMADO" and (
            self.nome or self.numero or self.autor or self.divulgacao_autorizada
        ):
            raise ValueError("Selecione o tipo do instrumento ou deixe seus dados em branco.")
        if self.divulgacao_autorizada and not self.nome:
            raise ValueError("Informe o nome do instrumento antes de autorizar a divulgação.")
        return self


class Brand(StrictModel):
    nome: str = Field(default="", max_length=160)
    uso_autorizado: bool = Field(default=False, strict=True)
    divulgacao_autorizada: bool = Field(default=False, strict=True)
    logo_id: str | None = Field(default=None, pattern=r"^[a-f0-9-]{36}$")

    @model_validator(mode="after")
    def authorized(self) -> Self:
        if (self.logo_id or self.divulgacao_autorizada) and not (self.nome and self.uso_autorizado):
            raise ValueError("Informe o parceiro e confirme a autorização de uso da marca.")
        return self


class InstitutionLink(Brand):
    instituicao_id: UUID | None = None
    nome: str = Field(min_length=2, max_length=160)
    tipo: Literal["ORGAO_GOVERNAMENTAL", "CLINICA", "ORGANIZACAO_EMPRESA", "OUTRO"]
    modalidade: Literal["TOTAL", "PARCIAL"] | None = None


class Institutional(StrictModel):
    apoio: Literal["TOTAL", "PARCIAL"] | None = None
    instrumento: Instrument = Field(default_factory=Instrument)
    governo: Brand = Field(default_factory=Brand)
    clinica: Brand = Field(default_factory=Brand)
    contratantes: list[InstitutionLink] = Field(default_factory=list, max_length=100)
    apoiadores: list[InstitutionLink] = Field(default_factory=list, max_length=100)


class BrandInput(Brand):
    # Arquivos são transitórios; o adaptador conserva somente a derivada PNG validada.
    conteudo_base64: str | None = Field(default=None, max_length=349528)

    @model_validator(mode="after")
    def upload_authorized(self) -> Self:
        if self.conteudo_base64 is not None and (
            self.logo_id or not self.nome or not self.uso_autorizado
        ):
            raise ValueError("Confirme a marca e seu uso antes de enviar uma nova imagem.")
        return self


class InstitutionLinkInput(InstitutionLink, BrandInput):
    pass


class InstitutionalInput(Institutional):
    governo: BrandInput = Field(default_factory=BrandInput)
    clinica: BrandInput = Field(default_factory=BrandInput)
    contratantes: list[InstitutionLinkInput] | None = Field(
        default=None, min_length=1, max_length=100
    )
    apoiadores: list[InstitutionLinkInput] | None = Field(
        default=None, min_length=1, max_length=100
    )

    @model_validator(mode="after")
    def roles_consistent(self) -> Self:
        for role in ("contratantes", "apoiadores"):
            links = getattr(self, role)
            if links is None:
                continue  # Edição de cliente legado conserva vínculos já existentes.
            keys = []
            for link in links:
                if role == "apoiadores" and link.modalidade is None:
                    raise ValueError("Informe total ou parcial para cada apoiador.")
                if role == "contratantes" and link.modalidade is not None:
                    raise ValueError("Modalidade de apoio pertence somente ao apoiador.")
                keys.append(
                    (
                        str(link.instituicao_id)
                        if link.instituicao_id
                        else " ".join(link.nome.casefold().split()),
                        link.tipo,
                    )
                )
            if len(keys) != len(set(keys)):
                raise ValueError("Remova instituições repetidas no mesmo papel.")
        return self
