import json
from contextlib import ExitStack
from uuid import uuid4

import pytest
from app.config import get_settings
from app.infrastructure.models import (
    ClinicalRecord,
    OperationalAccount,
    OperationalSession,
    Outbox,
    Participation,
)
from app.main import app
from conftest import PASSWORD
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_actions import create
from test_staff import assign, register

LOCAL_PASSWORD = "Senha-local-sintetica-2026!"
BASE = "/api/v1/operacao"


@pytest.fixture
def operational(authenticated, monkeypatch):
    admin, engine, _ = authenticated
    monkeypatch.setenv("OPERATIONAL_ACCESS_ENABLED", "true")
    monkeypatch.setenv("CLINICAL_FIELDS_ENABLED", "true")
    get_settings.cache_clear()
    action = create(admin)
    other = create(admin, nome="Outra ação sintética")
    staff = {}
    for category, username in [
        ("MEDICO", "oftalmo"),
        ("OPTOMETRISTA", "opto"),
        ("RECEPCAO", "recepcao"),
    ]:
        data = {"categoria": category, "nome": "Pessoa profissional " + username}
        if category != "RECEPCAO":
            data.update(
                registro_conselho="CRM" if category == "MEDICO" else "REGISTRO-TESTE",
                registro_numero=username,
                registro_uf="PB",
                habilitacao_validada=True,
                habilitacao_referencia="Validação sintética",
                registro_clinico_autorizado=True,
                autorizacao_clinica_referencia="Teste",
            )
        else:
            data.update(
                registro_conselho=None,
                registro_numero=None,
                registro_uf=None,
                habilitacao_validada=False,
                habilitacao_referencia="",
            )
        row = register(admin, **data)
        response = admin.put(
            f"/api/v1/profissionais/{row['id']}/acesso",
            json={
                "usuario": username,
                "nova_senha": LOCAL_PASSWORD,
                "senha_institucional": PASSWORD,
            },
        )
        assert response.status_code == 200, response.text
        assign(admin, action, row, locais_indices=[0] if category == "RECEPCAO" else None)
        staff[username] = row
    people = []
    for index in range(3):
        result = admin.post(
            f"/api/v1/acoes/{action['id']}/beneficiarios",
            json={
                "nome": f"Pessoa operacional {index}",
                "local_indice": index % 2,
            },
        )
        assert result.status_code == 201
    people = sorted(
        admin.get(f"/api/v1/acoes/{action['id']}/beneficiarios").json()["items"],
        key=lambda person: person["nome"],
    )
    for person, name in zip(people[:2], ["oftalmo", "opto"], strict=True):
        result = admin.put(
            f"/api/v1/acoes/{action['id']}/beneficiarios/{person['id']}/designacao-clinica",
            json={"profissional_id": staff[name]["id"]},
        )
        assert result.status_code == 200, result.text
    with ExitStack() as stack:
        clients = {}
        for name in staff:
            client = stack.enter_context(TestClient(app, raise_server_exceptions=False))
            client.headers["Origin"] = "http://localhost:3000"
            response = client.post(
                BASE + "/auth/login", json={"identifier": name, "password": LOCAL_PASSWORD}
            )
            assert response.status_code == 204, response.text
            me = client.get(BASE + "/auth/me").json()
            assert me["auth_source"] == "LOCAL" and me["agenda_url"] == ""
            client.headers["X-CSRF-Token"] = me["csrf_token"]
            clients[name] = client
        yield admin, engine, action, other, staff, people, clients


def test_operational_scope_reception_and_clinicians(operational):
    admin, _, action, other, _, people, clients = operational
    assignments = admin.get(f"/api/v1/acoes/{action['id']}/atribuicoes").json()["items"]
    assert all(row["conta_operacional_ativa"] for row in assignments)
    url = BASE + f"/acoes/{action['id']}"
    for client in clients.values():
        assert client.get(BASE + "/acoes").json()["total"] == 1
        assert client.get(BASE + f"/acoes/{other['id']}").status_code == 404
        for path in [
            "/indicadores",
            "/profissionais",
            "/instituicoes",
            "/tecnologia/saude",
            "/tecnologia/tokens",
            "/acoes",
        ]:
            assert client.get("/api/v1" + path).status_code in {401, 403}
    reception = clients["recepcao"]
    assert len(reception.get(url).json()["locais"]) == 1
    assert reception.get(url + "/beneficiarios").json()["total"] == 2
    assert reception.get(url + f"/beneficiarios/{people[1]['id']}").status_code == 404
    assert reception.get(url + f"/beneficiarios/{people[0]['id']}/clinica").status_code == 403
    assert (
        reception.put(
            url + f"/beneficiarios/{people[0]['id']}/clinica", json={"versao": 0, "campos": {}}
        ).status_code
        == 403
    )
    for index, name in enumerate(["oftalmo", "opto"]):
        client = clients[name]
        assert client.get(url + "/beneficiarios").json()["total"] == 1
        assert client.get(url + f"/beneficiarios/{people[index]['id']}").status_code == 200
        assert client.get(url + f"/beneficiarios/{people[1 - index]['id']}").status_code == 403
        assert (
            client.get(url + f"/beneficiarios/{people[1 - index]['id']}/clinica").status_code == 403
        )
        assert client.post(
            url + "/beneficiarios", json={"nome": "Teste", "local_indice": 0}
        ).status_code in {400, 403}
        assert client.get(url + "/profissionais").status_code == 403
    assert reception.get(url + "/profissionais").status_code == 200


def test_reception_registration_idempotency_csrf_assignment_and_no_export(operational, monkeypatch):
    dispatches = []
    monkeypatch.setattr("app.main.dispatch_safely", lambda: dispatches.append(True))
    admin, engine, action, _, staff, people, clients = operational
    client = clients["recepcao"]
    url = BASE + f"/acoes/{action['id']}/beneficiarios"
    data = {"nome": "CADASTRO_SINTETICO_NAO_EXPORTAR", "local_indice": 0}
    headers = {"Idempotency-Key": str(uuid4())}
    assert client.post(url, json=data).status_code == 400
    assert client.post(url, json={**data, "local_indice": 1}, headers=headers).status_code == 403
    token = client.headers.pop("X-CSRF-Token")
    assert client.post(url, json=data, headers=headers).status_code == 403
    client.headers["X-CSRF-Token"] = token
    first = client.post(url, json=data, headers=headers)
    assert first.status_code == 201, first.text
    assert dispatches
    again = client.post(url, json=data, headers=headers)
    assert again.status_code == 201 and again.json()["resultado"] == "existente"
    assert client.post(url, json={**data, "nome": "Alterado"}, headers=headers).status_code == 409
    target = people[2]
    designation = client.put(
        url + f"/{target['id']}/designacao-clinica",
        json={"profissional_id": staff["oftalmo"]["id"]},
    )
    assert designation.status_code == 200, designation.text
    clinical = clients["oftalmo"].put(
        url + f"/{target['id']}/clinica",
        json={
            "versao": 0,
            "campos": {"od": {"esferico": "CAMPO_CLINICO_SINTETICO"}},
        },
    )
    assert clinical.status_code == 200, clinical.text
    assert (
        clients["opto"].get(url + f"/{target['id']}/clinica", params={"versao": 1}).status_code
        == 403
    )
    with Session(engine) as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(Participation)
                .where(Participation.acao_id == action["id"])
            )
            == 4
        )
        record = session.scalar(select(ClinicalRecord))
        assert "CAMPO_CLINICO_SINTETICO" not in record.dados_cifrados
        for event in session.scalars(select(Outbox)):
            assert "CAMPO_CLINICO_SINTETICO" not in json.dumps(event.payload)
            assert "CADASTRO_SINTETICO_NAO_EXPORTAR" not in json.dumps(event.payload)
    assert admin.get("/api/v1/indicadores").status_code == 200


def test_local_account_reset_inactivation_and_audience(operational):
    admin, engine, _, _, staff, _, clients = operational
    client = clients["oftalmo"]
    cookie = client.cookies.get("ac_actions_operational")
    client.cookies.set("ac_actions_session", cookie)
    assert client.get("/api/v1/auth/me").status_code in {401, 403}
    url = f"/api/v1/profissionais/{staff['oftalmo']['id']}/acesso"
    reset = {
        "usuario": "oftalmo",
        "nova_senha": LOCAL_PASSWORD + "Nova",
        "senha_institucional": PASSWORD,
        "versao": 1,
    }
    assert admin.put(url, json={**reset, "senha_institucional": "incorreta"}).status_code == 401
    assert admin.put(url, json=reset).status_code == 200
    assert client.get(BASE + "/auth/me").status_code == 401
    assert (
        client.post(
            BASE + "/auth/login", json={"identifier": "oftalmo", "password": LOCAL_PASSWORD}
        ).status_code
        == 401
    )
    assert (
        client.post(
            BASE + "/auth/login",
            json={"identifier": "oftalmo", "password": LOCAL_PASSWORD + "Nova"},
        ).status_code
        == 204
    )
    assert admin.put(url, json={**reset, "versao": 2, "ativo": False}).status_code == 200
    assert client.get(BASE + "/auth/me").status_code == 401
    with Session(engine) as session:
        accounts = session.scalars(select(OperationalAccount)).all()
        assert all(LOCAL_PASSWORD not in row.senha_hash for row in accounts)
        assert session.scalar(select(func.count()).select_from(OperationalSession)) == 2


def test_operational_access_disabled_by_default(authenticated):
    client, _, _ = authenticated
    assert (
        client.post(
            BASE + "/auth/login", json={"identifier": "nobody", "password": LOCAL_PASSWORD}
        ).status_code
        == 503
    )


def test_operator_origin_rate_limit_and_logout(operational):
    _, _, _, _, _, _, clients = operational
    client = clients["recepcao"]
    credentials = {"identifier": "recepcao", "password": "Senha-incorreta-sintetica"}
    assert (
        client.post(
            BASE + "/auth/login",
            json=credentials,
            headers={"Origin": "https://wrong.example.invalid"},
        ).status_code
        == 403
    )
    for _ in range(5):
        assert client.post(BASE + "/auth/login", json=credentials).status_code == 401
    limited = client.post(BASE + "/auth/login", json=credentials)
    assert limited.status_code == 429 and limited.headers["retry-after"] == "600"
    assert client.post(BASE + "/auth/logout", json={}).status_code == 204
    assert client.get(BASE + "/auth/me").status_code == 401


def test_staff_inactivation_revokes_sessions_and_does_not_restore_assignments(operational):
    from app.domain.staff import StaffInput

    admin, _, _, _, staff, _, clients = operational
    row = staff["recepcao"]
    data = {key: value for key, value in row.items() if key in StaffInput.model_fields}
    url = f"/api/v1/profissionais/{row['id']}"
    assert admin.patch(url, json={**data, "versao": 1, "ativo": False}).status_code == 200
    client = clients["recepcao"]
    assert client.get(BASE + "/auth/me").status_code == 401
    assert admin.patch(url, json={**data, "versao": 2, "ativo": True}).status_code == 200
    assert client.get(BASE + "/auth/me").status_code == 401
    assert (
        client.post(
            BASE + "/auth/login", json={"identifier": "recepcao", "password": LOCAL_PASSWORD}
        ).status_code
        == 204
    )
    assert client.get(BASE + "/acoes").json()["total"] == 0


def test_account_collision_invalid_password_and_reception_cannot_manage_access(operational):
    admin, _, _, _, staff, _, clients = operational
    url = f"/api/v1/profissionais/{staff['opto']['id']}/acesso"
    data = {"usuario": "oftalmo", "versao": 1, "senha_institucional": PASSWORD}
    assert admin.put(url, json=data).status_code == 409
    assert (
        admin.put(url, json={**data, "usuario": "opto", "nova_senha": "curta"}).status_code == 422
    )
    assert clients["recepcao"].get(url).status_code in {401, 403}
    assert clients["recepcao"].put(url, json=data).status_code in {401, 403}
    current = admin.get(url).json()
    assert current == {"usuario": "opto", "versao": 1, "ativo": True}


def test_password_reset_blocks_request_already_authenticated(operational):
    from app.domain.contracts import Professional
    from app.infrastructure.operational_access import action_scope
    from fastapi import HTTPException

    admin, engine, action, _, staff, _, clients = operational
    response = clients["oftalmo"].get(BASE + "/auth/me").json()
    actor = Professional.model_validate(
        {key: value for key, value in response.items() if key in Professional.model_fields}
    )
    url = f"/api/v1/profissionais/{staff['oftalmo']['id']}/acesso"
    assert (
        admin.put(
            url, json={"usuario": "oftalmo", "versao": 1, "senha_institucional": PASSWORD}
        ).status_code
        == 200
    )
    with Session(engine) as session, session.begin(), pytest.raises(HTTPException) as caught:
        action_scope(session, action["id"], actor)
    assert caught.value.status_code == 403
