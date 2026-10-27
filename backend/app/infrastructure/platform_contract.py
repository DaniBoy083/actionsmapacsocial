"""Validate the confirmed 1.2.0 producer projection; never forward raw records."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.contracts import MUNICIPALITIES as CATALOG

Count = Annotated[int, Field(strict=True, ge=0, le=2**53 - 1)]
Filter = Literal[
    "ano",
    "mes",
    "status",
    "servico",
    "eixoDemografico",
    "categoriaDemografica",
    "servicosExcluidos",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)


class Totals(Contract):
    quantidadeAcoes: Count
    quantidadeParticipacoes: Count
    quantidadePessoasContempladas: Count

    @model_validator(mode="after")
    def consistent_people(self):
        if self.quantidadePessoasContempladas > self.quantidadeParticipacoes:
            raise ValueError("People exceed participations")
        if self.quantidadeAcoes == 0 and (
            self.quantidadeParticipacoes or self.quantidadePessoasContempladas
        ):
            raise ValueError("Counts without actions")
        return self


class Municipality(Contract):
    ibge: str = Field(pattern=r"^25[0-9]{5}$")
    nome: str = Field(min_length=1, max_length=200)
    uf: Literal["PB"]
    quantidadeAcoes: Count
    acoesSemDistribuicao: Count
    participacoesMunicipioUnico: Count
    pessoasContempladasMunicipioUnico: Count

    @model_validator(mode="after")
    def consistent_municipality(self):
        if self.ibge not in CATALOG or self.nome != CATALOG[self.ibge]:
            raise ValueError("Unknown or inconsistent municipality")
        if not self.quantidadeAcoes or self.acoesSemDistribuicao > self.quantidadeAcoes:
            raise ValueError("Inconsistent action counts")
        if self.pessoasContempladasMunicipioUnico > self.participacoesMunicipioUnico:
            raise ValueError("People exceed participations")
        if self.acoesSemDistribuicao == self.quantidadeAcoes and (
            self.participacoesMunicipioUnico or self.pessoasContempladasMunicipioUnico
        ):
            raise ValueError("Municipal allocation without single-city actions")
        return self


class Aggregates(Totals):
    quantidadeMunicipios: int = Field(ge=0, le=223)
    acoesSemData: Count
    municipios: list[Municipality] = Field(max_length=223)
    semDistribuicaoMunicipal: Totals

    @model_validator(mode="after")
    def consistent_aggregation(self):
        rows, multi = self.municipios, self.semDistribuicaoMunicipal
        if self.quantidadeMunicipios != len(rows) or len({row.ibge for row in rows}) != len(rows):
            raise ValueError("Duplicate or inconsistent municipalities")
        if bool(self.quantidadeAcoes) != bool(rows) or self.acoesSemData > self.quantidadeAcoes:
            raise ValueError("Inconsistent coverage")
        for field in Totals.model_fields:
            if getattr(multi, field) > getattr(self, field):
                raise ValueError("Unallocated totals exceed global totals")
        if any(
            row.quantidadeAcoes > self.quantidadeAcoes
            or row.acoesSemDistribuicao > multi.quantidadeAcoes
            for row in rows
        ):
            raise ValueError("Municipal action count exceeds global count")
        single_actions = sum(row.quantidadeAcoes - row.acoesSemDistribuicao for row in rows)
        multi_presences = sum(row.acoesSemDistribuicao for row in rows)
        if single_actions + multi.quantidadeAcoes != self.quantidadeAcoes:
            raise ValueError("Action distribution is inconsistent")
        if not 2 * multi.quantidadeAcoes <= multi_presences <= 223 * multi.quantidadeAcoes:
            raise ValueError("Multiple-city distribution is inconsistent")
        if (
            sum(row.participacoesMunicipioUnico for row in rows) + multi.quantidadeParticipacoes
            != self.quantidadeParticipacoes
        ):
            raise ValueError("Participation distribution is inconsistent")
        if (
            sum(row.pessoasContempladasMunicipioUnico for row in rows)
            + multi.quantidadePessoasContempladas
            != self.quantidadePessoasContempladas
        ):
            raise ValueError("People distribution is inconsistent")
        return self


class Scope(Contract):
    tipo: Literal["acoes_publicadas_na_origem"]
    filtrosAplicados: list[str] = Field(max_length=0)
    filtrosNaoAplicados: list[Filter] = Field(max_length=7)
    pessoas: Literal["contempladas nas ações, sem deduplicação entre ações"]

    @model_validator(mode="after")
    def unique_filters(self):
        if len(self.filtrosNaoAplicados) != len(set(self.filtrosNaoAplicados)):
            raise ValueError("Duplicate filters")
        return self


class ActionsBlock(Contract):
    versaoCalculo: Literal["1.0"]
    fonte: Literal["ac-actions-map"]
    escopo: Scope
    status: Literal["disponivel", "indisponivel"]
    codigo: (
        Literal[
            "CONFIGURACAO_AUSENTE",
            "CONFIGURACAO_INVALIDA",
            "LIMITE_ORIGEM",
            "EXPORTACAO_EXPIRADA",
            "CONTRATO_INVALIDO",
            "ORIGEM_INDISPONIVEL",
            "LIMITE_PAYLOAD",
        ]
        | None
    )
    geracao: str | None = Field(pattern=r"^[1-9][0-9]{0,18}$")
    capturadoEmIso: str | None = Field(max_length=64)
    expiraEmIso: str | None = Field(max_length=64)
    dados: Aggregates | None


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Timezone required")
    return result


def unavailable_actions(status: str, checked_at: str) -> dict:
    return {
        "status": status,
        "checked_at": checked_at,
        "refresh_after_seconds": 30,
        "generation": None,
        "captured_at": None,
        "expires_at": None,
        "summary": None,
        "municipalities": [],
    }


def totals(value: Totals) -> dict:
    return {
        "action_count": value.quantidadeAcoes,
        "participation_count": value.quantidadeParticipacoes,
        "people_count": value.quantidadePessoasContempladas,
    }


def approved_actions(payload: object, checked_at: str, *, now: datetime | None = None) -> dict:
    if not isinstance(payload, dict) or payload.get("versao") != "1":
        raise ValueError("Unsupported analytics envelope")
    if "acoesInstitucionais" not in payload:
        return unavailable_actions("contract_unavailable", checked_at)
    block = ActionsBlock.model_validate(payload["acoesInstitucionais"])
    if block.status == "indisponivel":
        if block.codigo is None or any(
            value is not None
            for value in (block.geracao, block.capturadoEmIso, block.expiraEmIso, block.dados)
        ):
            raise ValueError("Inconsistent unavailable snapshot")
        return unavailable_actions("unavailable", checked_at)
    if block.codigo is not None or any(
        value is None
        for value in (block.geracao, block.capturadoEmIso, block.expiraEmIso, block.dados)
    ):
        raise ValueError("Incomplete available snapshot")
    current = now or datetime.now(UTC)
    captured, expires = instant(block.capturadoEmIso), instant(block.expiraEmIso)
    if captured > current + timedelta(seconds=60) or expires <= current or expires <= captured:
        raise ValueError("Expired or future snapshot")
    data = block.dados
    return {
        "status": "available" if data.quantidadeAcoes else "empty",
        "checked_at": checked_at,
        "refresh_after_seconds": 60,
        "generation": block.geracao,
        "captured_at": block.capturadoEmIso,
        "expires_at": block.expiraEmIso,
        "summary": {
            **totals(data),
            "municipality_count": data.quantidadeMunicipios,
            "undated_action_count": data.acoesSemData,
            "unallocated": totals(data.semDistribuicaoMunicipal),
        },
        "municipalities": [
            {
                "code": row.ibge,
                "name": CATALOG[row.ibge],
                "action_count": row.quantidadeAcoes,
                "unallocated_action_count": row.acoesSemDistribuicao,
                "single_municipality_participations": row.participacoesMunicipioUnico,
                "single_municipality_people": row.pessoasContempladasMunicipioUnico,
            }
            for row in sorted(data.municipios, key=lambda row: row.ibge)
        ],
    }
