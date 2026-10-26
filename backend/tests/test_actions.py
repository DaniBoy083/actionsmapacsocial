import json

import pytest
from app.infrastructure.models import Audit, Beneficiary, ImportBatch, Outbox
from conftest import PASSWORD
from sqlalchemy import select
from sqlalchemy.orm import Session

ACTION = {
    "nome": "Ação de teste",
    "locais": [
        {"municipio_ibge": "2507507", "nome_local": "Unidade A"},
        {"municipio_ibge": "2504009", "nome_local": "Unidade B"},
    ],
}


def create(client, **values):
    response = client.post("/api/v1/acoes", json={**ACTION, **values})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize(
    "route",
    [
        "/acoes",
        "/indicadores",
        "/localidades/pb",
        "/tecnologia/saude",
        "/acoes/unknown",
        "/importacoes/unknown/paginas/1",
    ],
)
def test_anonymous_rejected(api_client, route):
    client, _, _ = api_client
    assert client.get("/api/v1" + route).status_code == 401


def test_login_has_secure_session_and_no_password_leak(authenticated):
    client, _, _ = authenticated
    me = client.get("/api/v1/auth/me")
    assert me.headers["cache-control"] == "no-store"
    assert "password" not in me.text and PASSWORD not in me.text
    assert me.json()["equipe"] == "tecnologia"


@pytest.mark.parametrize(
    "team,kind",
    [("outro", "administracao"), ("tecnologia", "terapia_aba"), ("administracao", "recepcao")],
)
def test_login_requires_kind_and_team(api_client, team, kind):
    client, _, repo = api_client
    repo.professional.equipe, repo.professional.tipo_login = team, kind
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "test@example.invalid", "password": PASSWORD},
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 403


def test_login_origin_password_and_limits(api_client):
    client, _, _ = api_client
    payload = {"identifier": "test@example.invalid", "password": "wrong"}
    assert client.post("/api/v1/auth/login", json=payload).status_code == 403
    for _ in range(5):
        assert (
            client.post(
                "/api/v1/auth/login", json=payload, headers={"Origin": "http://localhost:3000"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/v1/auth/login", json=payload, headers={"Origin": "http://localhost:3000"}
        ).status_code
        == 429
    )


def test_access_revoked_on_team_change(authenticated):
    client, _, repo = authenticated
    repo.professional.equipe = "outro"
    assert client.get("/api/v1/acoes").status_code == 403
    assert client.get("/api/v1/acoes").status_code == 401


def test_technical_route_rejects_administration(authenticated):
    client, _, repo = authenticated
    repo.professional.equipe = "administracao"
    assert client.get("/api/v1/tecnologia/saude").status_code == 403
    assert client.get("/api/v1/acoes").status_code == 200


def test_csrf_required(authenticated):
    client, _, _ = authenticated
    del client.headers["X-CSRF-Token"]
    assert client.post("/api/v1/acoes", json=ACTION).status_code == 403


def test_crud_multi_locations_filters_archive_and_audit(authenticated):
    client, engine, _ = authenticated
    action = create(client)
    assert len(action["locais"]) == 2
    indicators = client.get("/api/v1/indicadores").json()
    assert indicators["acoes"] == 1 and indicators["municipios"] == 2
    assert sum(p["acoes"] for p in indicators["por_municipio"]) == 2
    assert client.get("/api/v1/acoes", params={"municipio": "2504009"}).json()["total"] == 1
    assert client.get("/api/v1/acoes", params={"busca": "inexistente"}).json()["total"] == 0
    updated = client.patch(
        "/api/v1/acoes/" + action["id"], json={**ACTION, "nome": "Editada", "versao": 1}
    )
    assert updated.status_code == 200 and updated.json()["versao"] == 2
    assert (
        client.patch("/api/v1/acoes/" + action["id"], json={**ACTION, "versao": 1}).status_code
        == 409
    )
    assert (
        client.request("DELETE", "/api/v1/acoes/" + action["id"], json={"versao": 2}).status_code
        == 200
    )
    assert client.get("/api/v1/indicadores").json()["acoes"] == 0
    assert client.get("/api/v1/acoes").json()["items"][0]["status"] == "arquivada"
    with Session(engine) as session:
        assert len(session.scalars(select(Audit)).all()) >= 4


@pytest.mark.parametrize(
    "changes",
    [
        {"locais": [{"municipio_ibge": "9999999"}]},
        {"locais": []},
        {"locais": [ACTION["locais"][0], ACTION["locais"][0]]},
        {"inicio_em": "2026-10-20", "fim_em": "2026-10-01"},
        {"fim_em": "2026-10-01"},
        {"nome": "x"},
        {"cpf": "private"},
    ],
)
def test_invalid_actions_rejected(authenticated, changes):
    client, _, _ = authenticated
    response = client.post("/api/v1/acoes", json={**ACTION, **changes})
    assert response.status_code == 422
    assert "private" not in response.text


def test_beneficiary_encrypted_and_outbox_excludes_pii(authenticated):
    client, engine, _ = authenticated
    action = create(client)
    response = client.post(
        f"/api/v1/acoes/{action['id']}/beneficiarios",
        json={"nome": "Pessoa Sintética", "municipio_residencia_ibge": "2507507"},
    )
    assert response.status_code == 201
    people = client.get(f"/api/v1/acoes/{action['id']}/beneficiarios").json()
    assert people["items"][0]["nome"] == "Pessoa Sintética"
    assert client.get("/api/v1/indicadores").json()["participacoes"] == 1
    with Session(engine) as session:
        person = session.scalar(select(Beneficiary))
        assert "Pessoa Sintética" not in person.dados_cifrados
        for row in session.scalars(select(Outbox)):
            payload = json.dumps(row.payload)
            for forbidden in [
                "Pessoa Sintética",
                "cpf",
                "usuario_id",
                "beneficiario_id",
                "nome",
                "telefone",
                "descricao",
            ]:
                assert forbidden not in payload
            assert row.payload["publicavel"] is False


def test_publication_requires_workflow_and_real_integration(authenticated):
    client, _, _ = authenticated
    action = create(client, resumo_publico="Resumo editorial para revisão.")
    url = f"/api/v1/acoes/{action['id']}"
    assert action["status"] == "em_revisao"
    assert client.post(url + "/publicar", json={"versao": 1}).status_code == 503
    assert client.post(url + "/aprovar", json={"versao": 1}).status_code == 200
    assert client.post(url + "/publicar", json={"versao": 2}).status_code == 503
    edited = client.patch(url, json={**ACTION, "versao": 2})
    assert edited.json()["status"] == "em_revisao" and edited.json()["aprovado_por"] is None


def test_import_idempotency_and_transaction(authenticated):
    client, engine, repo = authenticated
    action = create(client)
    with Session(engine) as session, session.begin():
        batch = ImportBatch(
            hash_arquivo="a" * 64, paginas=2, autor_id=repo.professional.profissional_id
        )
        session.add(batch)
        session.flush()
        identifier = batch.id
    data = {
        "importacao_id": identifier,
        "acao_id": action["id"],
        "registros": [
            {"pagina": 1, "nome": "Pessoa Sintética", "revisado": True},
        ],
    }
    response = client.post("/api/v1/importacoes/confirmar", json=data)
    assert response.status_code == 200, response.text
    assert response.json()["incluidos"] == 1
    assert client.post("/api/v1/importacoes/confirmar", json=data).json()["existentes"] == 1
    assert client.get("/api/v1/indicadores").json()["participacoes"] == 1
    data["registros"] = [
        {"pagina": 2, "nome": "Pessoa B", "revisado": True},
        {"pagina": 3, "nome": "Pessoa C", "revisado": True},
    ]
    assert client.post("/api/v1/importacoes/confirmar", json=data).status_code == 422
    assert client.get("/api/v1/indicadores").json()["participacoes"] == 1


def test_session_expiration_and_logout(authenticated):
    client, _engine, _ = authenticated
    assert client.post("/api/v1/auth/logout", json={}).status_code == 204
    assert client.get("/api/v1/acoes").status_code == 401


def test_successful_logins_do_not_accumulate_account_failures(api_client):
    client, _, _ = api_client
    for _ in range(6):
        response = client.post(
            "/api/v1/auth/login",
            json={"identifier": "test@example.invalid", "password": PASSWORD},
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 204
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "SameSite=strict" in response.headers["set-cookie"]


def test_separate_venues_in_same_municipality_are_valid(authenticated):
    client, _, _ = authenticated
    action = create(
        client,
        locais=[
            {"municipio_ibge": "2507507", "nome_local": "Local A"},
            {"municipio_ibge": "2507507", "nome_local": "Local B"},
        ],
    )
    assert len(action["locais"]) == 2
    result = client.get("/api/v1/indicadores").json()
    assert result["acoes"] == 1 and result["municipios"] == 1


def test_archive_preserves_beneficiaries_and_replaces_summary(authenticated):
    client, engine, _ = authenticated
    action = create(client)
    url = f"/api/v1/acoes/{action['id']}"
    assert client.post(url + "/beneficiarios", json={"nome": "Pessoa Sintética"}).status_code == 201
    assert client.request("DELETE", url, json={"versao": 2}).status_code == 200
    assert client.get(url + "/beneficiarios").json()["total"] == 1
    assert client.get("/api/v1/indicadores").json()["participacoes"] == 0
    with Session(engine) as session:
        summary = session.scalar(select(Outbox).where(Outbox.idempotency_key.endswith(":v3")))
        assert summary.payload["operacao"] == "archive"
        assert summary.payload["quantidade_acoes"] == 0
        assert summary.payload["quantidade_participacoes"] == 0


def test_validation_never_echoes_credentials(api_client):
    client, _, _ = api_client
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "", "password": "secret-value", "extra": "private-value"},
    )
    assert response.status_code == 422
    assert "secret-value" not in response.text and "private-value" not in response.text
