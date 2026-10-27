import asyncio
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from app.api.published_map import platform_source
from app.domain.contracts import MUNICIPALITIES
from app.domain.published_map import PublishedMap
from app.infrastructure.platform_contract import approved_actions
from app.infrastructure.published_map import (
    MAX_BYTES,
    PlatformPublishedMap,
    approved_url,
    retry_delay,
)
from app.main import app
from published_map_fixture import actions_payload

URL = "https://plataforma-consolidada-de-analise-d.vercel.app/api/v1/analytics"


def test_official_geometry_catalog_matches_all_223_validated_municipalities():
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "src/data/paraiba-map.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(data["municipalities"]) == 223
    assert {r["id"]: r["name"] for r in data["municipalities"]} == MUNICIPALITIES


def test_only_aggregates_are_projected_without_duplicating_people_between_cities():
    payload = actions_payload(generation="9007199254740993")
    payload["private_clinical"] = {"name": "PRIVATE-MARKER"}
    data = PublishedMap.model_validate(approved_actions(payload, datetime.now(UTC).isoformat()))
    assert data.generation == "9007199254740993"
    assert data.summary.action_count == 2
    assert sum(r.action_count for r in data.municipalities) == 3
    assert sum(r.single_municipality_people for r in data.municipalities) == 10
    assert data.summary.people_count == 17 and data.summary.unallocated.people_count == 7
    assert "PRIVATE-MARKER" not in data.model_dump_json()
    assert approved_actions(actions_payload(empty=True), "checked")["status"] == "empty"
    assert approved_actions({"versao": "1"}, "checked")["status"] == "contract_unavailable"


@pytest.mark.parametrize("value", [-1, True, 1.2, float("nan"), 2**53, "2"])
def test_counts_are_strict_safe_nonnegative_integers(value):
    payload = actions_payload()
    payload["acoesInstitucionais"]["dados"]["quantidadeAcoes"] = value
    with pytest.raises(ValueError):
        approved_actions(payload, "checked")


@pytest.mark.parametrize(
    "case",
    [
        "personal",
        "missing",
        "unknown_city",
        "wrong_name",
        "wrong_state",
        "duplicate",
        "people",
        "municipal_people",
        "distribution",
        "multi_total",
        "single_total",
        "undated",
        "municipal_count",
        "expired",
        "future",
        "timezone",
        "expiry_order",
        "generation",
        "filters",
        "version",
        "unavailable_with_data",
        "too_many_cities",
    ],
)
def test_invalid_or_private_payload_is_rejected(case):
    payload = actions_payload()
    block = payload["acoesInstitucionais"]
    data = block["dados"]
    row = data["municipios"][0]
    if case == "personal":
        row["nomeBeneficiario"] = "PRIVATE-MARKER"
    elif case == "missing":
        del row["quantidadeAcoes"]
    elif case == "unknown_city":
        row["ibge"] = "2599999"
    elif case == "wrong_name":
        row["nome"] = "<script>PRIVATE-MARKER</script>"
    elif case == "wrong_state":
        row["uf"] = "PE"
    elif case == "duplicate":
        data["municipios"][1] = row
    elif case == "people":
        data["quantidadePessoasContempladas"] = 22
    elif case == "municipal_people":
        row["pessoasContempladasMunicipioUnico"] = 13
    elif case == "distribution":
        data["municipios"][1]["acoesSemDistribuicao"] = 0
    elif case == "multi_total":
        data["semDistribuicaoMunicipal"]["quantidadeAcoes"] = 3
    elif case == "single_total":
        row["participacoesMunicipioUnico"] = 13
    elif case == "undated":
        data["acoesSemData"] = 3
    elif case == "municipal_count":
        data["quantidadeMunicipios"] = 3
    elif case == "expired":
        block["expiraEmIso"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    elif case == "future":
        block["capturadoEmIso"] = (datetime.now(UTC) + timedelta(minutes=2)).isoformat()
    elif case == "timezone":
        block["capturadoEmIso"] = "2026-10-27T12:00:00"
    elif case == "expiry_order":
        block["expiraEmIso"] = block["capturadoEmIso"]
    elif case == "generation":
        block["geracao"] = "01"
    elif case == "filters":
        block["escopo"]["filtrosAplicados"] = ["ano"]
    elif case == "version":
        block["versaoCalculo"] = "2.0"
    elif case == "unavailable_with_data":
        block.update(status="indisponivel", codigo="ORIGEM_INDISPONIVEL")
    elif case == "too_many_cities":
        data["municipios"] *= 112
    with pytest.raises(ValueError):
        approved_actions(payload, "checked")


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/api/v1/analytics",
        URL + "?token=secret",
        URL + "#fragment",
        URL.replace("https://", "https://user:password@"),
        URL.replace(".app/", ".app:444/"),
        URL.replace("analytics", "other"),
        "https://attacker.invalid/api/v1/analytics",
        URL.replace(".app/", ".app.attacker.invalid/"),
        "https://[invalid",
    ],
)
def test_unapproved_urls_are_never_requested(url):
    assert not approved_url(url)

    async def run():
        def unexpected(_):
            pytest.fail("Unapproved network request")

        source = PlatformPublishedMap(url, "synthetic-key", httpx.MockTransport(unexpected))
        assert (await source.read()).status == "not_configured"

    asyncio.run(run())


@pytest.mark.parametrize("status", [301, 401, 403, 404, 429, 500, 503])
def test_http_failures_are_sanitized_cached_and_never_become_zero(status, caplog):
    async def run():
        calls = []

        def handler(request):
            calls.append(request)
            assert request.headers["x-api-key"] == "synthetic-secret-key"
            return httpx.Response(
                status,
                text="PRIVATE-MARKER",
                headers={"Retry-After": "90", "Location": "https://attacker.invalid"},
            )

        source = PlatformPublishedMap(URL, "synthetic-secret-key", httpx.MockTransport(handler))
        result = await source.read()
        assert result.status == ("unauthorized" if status in {401, 403} else "unavailable")
        assert result.summary is None and not result.municipalities
        assert (await source.read()) == result and len(calls) == 1
        if status in {429, 503}:
            assert result.refresh_after_seconds == 90
        assert "PRIVATE-MARKER" not in result.model_dump_json() + caplog.text
        assert "synthetic-secret-key" not in result.model_dump_json() + caplog.text

    asyncio.run(run())


@pytest.mark.parametrize("case", ["html", "duplicate_json", "oversized", "timeout", "bad_json"])
def test_response_bounds_and_timeout(case):
    async def run():
        def handler(_):
            if case == "timeout":
                raise httpx.ReadTimeout("PRIVATE-MARKER")
            if case == "html":
                return httpx.Response(200, text="<html>PRIVATE-MARKER</html>")
            if case == "duplicate_json":
                return httpx.Response(
                    200,
                    content=b'{"versao":"1","versao":"2"}',
                    headers={"content-type": "application/json"},
                )
            if case == "oversized":
                return httpx.Response(
                    200,
                    content=b" " * (MAX_BYTES + 1),
                    headers={"content-type": "application/json"},
                )
            return httpx.Response(
                200, content=b"bad-json", headers={"content-type": "application/json"}
            )

        source = PlatformPublishedMap(URL, "synthetic-key", httpx.MockTransport(handler))
        assert (await source.read()).status == "unavailable"

    asyncio.run(run())


def test_single_flight_cache_generation_precision_conflict_and_recovery():
    async def run():
        payload = actions_payload(generation="9007199254740993")
        calls = []

        async def handler(request):
            calls.append(request)
            await asyncio.sleep(0)
            return httpx.Response(200, json=payload)

        source = PlatformPublishedMap(URL, "synthetic-key", httpx.MockTransport(handler))
        results = await asyncio.gather(*(source.read() for _ in range(8)))
        assert all(r.status == "available" for r in results) and len(calls) == 1
        assert 0 < source.until - time.monotonic() <= 60
        results[0].municipalities.clear()
        assert len((await source.read()).municipalities) == 2
        payload["acoesInstitucionais"]["geracao"] = "9007199254740992"
        source.until = 0
        assert (await source.read()).status == "unavailable"
        payload["acoesInstitucionais"]["geracao"] = "9007199254740993"
        source.until = 0
        assert (await source.read()).status == "available"
        payload["acoesInstitucionais"]["dados"]["acoesSemData"] = 0
        source.until = 0
        assert (await source.read()).status == "unavailable"
        payload["acoesInstitucionais"]["geracao"] = "9007199254740994"
        source.until = 0
        assert (await source.read()).status == "available"

    asyncio.run(run())


def test_expired_cache_is_removed_even_with_unexpired_monotonic_ttl():
    async def run():
        source = PlatformPublishedMap(
            URL, "key", httpx.MockTransport(lambda _: httpx.Response(200, json=actions_payload()))
        )
        assert (await source.read()).status == "available"
        source.cached.expires_at = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
        assert source.current_cache() is None

    asyncio.run(run())


def test_retry_after_bounds_and_date():
    assert retry_delay("99999999999999999") == 86400
    assert retry_delay("1") == 30
    assert retry_delay("bad") == 60
    assert 30 <= retry_delay("Wed, 01 Jan 2020 00:00:00 GMT") <= 60


def test_map_requires_revalidated_institutional_session_before_request(api_client):
    client, _, _ = api_client
    app.dependency_overrides[platform_source] = lambda: pytest.fail("No network before login")
    assert client.get("/api/v1/mapa-acoes").status_code == 401


def test_map_allows_administration_and_revokes_access_when_identity_changes(authenticated):
    client, _, identities = authenticated

    class FakeSource:
        async def read(self):
            return PublishedMap.model_validate(
                approved_actions(actions_payload(), datetime.now(UTC).isoformat())
            )

    app.dependency_overrides[platform_source] = FakeSource
    identities.professional = identities.professional.model_copy(update={"equipe": "administracao"})
    result = client.get("/api/v1/mapa-acoes")
    assert result.status_code == 200 and result.json()["summary"]["action_count"] == 2
    assert result.headers["Cache-Control"] == "no-store"
    identities.professional = identities.professional.model_copy(update={"equipe": "outra"})
    assert client.get("/api/v1/mapa-acoes").status_code == 403
