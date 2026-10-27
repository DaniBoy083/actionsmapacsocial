"""Synthetic, consistent municipal projection. No production counts or records."""

from datetime import UTC, datetime, timedelta


def actions_block(*, empty=False, now=None, generation="1", lifetime=900):
    captured = now or datetime.now(UTC)
    data = {
        "quantidadeAcoes": 2,
        "quantidadeParticipacoes": 21,
        "quantidadePessoasContempladas": 17,
        "quantidadeMunicipios": 2,
        "acoesSemData": 1,
        "municipios": [
            {
                "ibge": "2507507",
                "nome": "João Pessoa",
                "uf": "PB",
                "quantidadeAcoes": 2,
                "acoesSemDistribuicao": 1,
                "participacoesMunicipioUnico": 12,
                "pessoasContempladasMunicipioUnico": 10,
            },
            {
                "ibge": "2503209",
                "nome": "Cabedelo",
                "uf": "PB",
                "quantidadeAcoes": 1,
                "acoesSemDistribuicao": 1,
                "participacoesMunicipioUnico": 0,
                "pessoasContempladasMunicipioUnico": 0,
            },
        ],
        "semDistribuicaoMunicipal": {
            "quantidadeAcoes": 1,
            "quantidadeParticipacoes": 9,
            "quantidadePessoasContempladas": 7,
        },
    }
    if empty:
        data = {
            key: 0
            for key in [
                "quantidadeAcoes",
                "quantidadeParticipacoes",
                "quantidadePessoasContempladas",
                "quantidadeMunicipios",
                "acoesSemData",
            ]
        }
        data.update(
            municipios=[],
            semDistribuicaoMunicipal={
                "quantidadeAcoes": 0,
                "quantidadeParticipacoes": 0,
                "quantidadePessoasContempladas": 0,
            },
        )
    return {
        "versaoCalculo": "1.0",
        "fonte": "ac-actions-map",
        "status": "disponivel",
        "codigo": None,
        "geracao": generation,
        "capturadoEmIso": captured.isoformat(),
        "expiraEmIso": (captured + timedelta(seconds=lifetime)).isoformat(),
        "dados": data,
        "escopo": {
            "tipo": "acoes_publicadas_na_origem",
            "filtrosAplicados": [],
            "filtrosNaoAplicados": [],
            "pessoas": "contempladas nas ações, sem deduplicação entre ações",
        },
    }


def actions_payload(**kwargs):
    payload = {"versao": "1"}
    payload["acoesInstitucionais"] = actions_block(**kwargs)
    return payload
