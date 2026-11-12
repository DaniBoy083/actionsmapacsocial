import json
import sqlite3

import pytest
from app.infrastructure.local_migrations import add_local_staff
from app.infrastructure.models import (
    Base,
    ClinicalRecord,
    ClinicalRevision,
    Outbox,
    StaffAssignment,
    StaffRecord,
    StaffRevision,
)
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session
from test_actions import ACTION, create

MEDIC = {
    "nome": "Profissional sintético",
    "categoria": "MEDICO",
    "registro_conselho": "CRM",
    "registro_numero": "000123",
    "registro_uf": "PB",
    "habilitacao_validada": True,
    "habilitacao_referencia": "Conferência sintética de teste",
}
RECEPTION = {"nome": "Recepção sintética", "categoria": "RECEPCAO"}


def register(client, **changes):
    response = client.post("/api/v1/profissionais", json={**MEDIC, **changes})
    assert response.status_code == 201, response.text
    return response.json()


def assign(client, action, staff, **changes):
    response = client.post(
        f"/api/v1/acoes/{action['id']}/atribuicoes",
        json={
            "profissional_id": staff["id"],
            "acao_versao": action["versao"],
            "profissional_versao": staff["versao"],
            **changes,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize("team", ["administracao", "tecnologia"])
def test_staff_registry_versions_manual_verification_and_no_export(authenticated, team):
    client, engine, repo = authenticated
    repo.professional.equipe = team
    staff = register(client)
    assert staff["conferido_por"] == repo.professional.profissional_id
    assert staff["conferido_em"]
    assert staff["divulgacao_autorizada"] is False
    assert staff["registro_numero"] == "000123"
    url = f"/api/v1/profissionais/{staff['id']}"
    assert client.get(url).status_code == 200
    assert client.get(url).headers["cache-control"] == "no-store"
    assert client.get("/api/v1/profissionais", params={"busca": "%"}).json()["total"] == 0
    changed = client.patch(url, json={**MEDIC, "versao": 1, "nome": "Nome atualizado"})
    assert changed.status_code == 200
    assert changed.json()["versao"] == 2
    assert client.patch(url, json={**MEDIC, "versao": 1}).status_code == 409
    history = client.get(url + "/historico").json()
    assert history["total"] == 2
    assert history["items"][1]["dados"]["nome"] == MEDIC["nome"]
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Outbox)) == 0
        assert session.scalar(select(func.count()).select_from(StaffRevision)) == 2


@pytest.mark.parametrize(
    "change",
    [
        {"registro_uf": "XX"},
        {"registro_conselho": "OUTRO"},
        {"registro_numero": None},
        {"habilitacao_referencia": ""},
        {"categoria": "OUTRO"},
        {"categoria": "OPTOMETRISTA"},
        {"categoria": "RECEPCAO"},
        {"ativo": "true"},
        {"divulgacao_autorizada": True},
        {"cpf_paciente": "PRIVATE_SENTINEL"},
        {"nome": "x"},
        {"versao": True},
    ],
)
def test_staff_validation_minimizes_data_and_does_not_echo_values(authenticated, change):
    client, _, _ = authenticated
    response = client.post("/api/v1/profissionais", json={**MEDIC, **change})
    assert response.status_code in {409, 422}
    assert "PRIVATE_SENTINEL" not in response.text


def test_registry_does_not_merge_names_or_duplicate_registration(authenticated):
    client, _, _ = authenticated
    first = register(client)
    assert client.post("/api/v1/profissionais", json=MEDIC).status_code == 409
    second = register(client, registro_numero="000124")
    assert first["id"] != second["id"]
    duplicate = client.patch(f"/api/v1/profissionais/{second['id']}", json={**MEDIC, "versao": 1})
    assert duplicate.status_code == 409
    assert client.get("/api/v1/profissionais").json()["total"] == 2
    assert client.post("/api/v1/profissionais", json=RECEPTION).status_code == 201
    assert client.post("/api/v1/profissionais", json=RECEPTION).status_code == 201


def test_optometrist_registration_is_not_medical_and_publication_is_opt_in(authenticated):
    client, _, _ = authenticated
    data = {**MEDIC, "categoria": "OPTOMETRISTA", "registro_conselho": "ÓRGÃO SINTÉTICO"}
    assert client.post("/api/v1/profissionais", json=data).status_code == 201
    assert client.post("/api/v1/profissionais", json={**data, "rqe": "123"}).status_code == 422
    doctor = register(
        client, divulgacao_autorizada=True, divulgacao_referencia="Autorização sintética"
    )
    assert doctor["divulgacao_registrada_por"] and doctor["divulgacao_registrada_em"]


def test_assignment_scope_versions_and_cross_action_access(authenticated):
    client, engine, _ = authenticated
    first, other, staff = create(client), create(client), register(client)
    row = assign(client, first, staff, locais_indices=[1, 0])
    assert row["locais_indices"] == [0, 1]
    assert row["locais_snapshot"][0]["municipio_ibge"] == ACTION["locais"][0]["municipio_ibge"]
    assert row["profissional_snapshot"]["nome"] == staff["nome"]
    duplicate = client.post(
        f"/api/v1/acoes/{first['id']}/atribuicoes",
        json={
            "profissional_id": staff["id"],
            "acao_versao": 1,
            "profissional_versao": 1,
        },
    )
    assert duplicate.status_code == 409
    patch = {
        "versao": 1,
        "acao_versao": 1,
        "profissional_versao": 1,
        "ativo": True,
        "locais_indices": [0],
    }
    url = f"/api/v1/acoes/{first['id']}/atribuicoes/{row['id']}"
    assert (
        client.patch(f"/api/v1/acoes/{other['id']}/atribuicoes/{row['id']}", json=patch).status_code
        == 404
    )
    assert client.patch(url, json=patch).json()["versao"] == 2
    assert client.patch(url, json=patch).status_code == 409
    history_url = url + "/historico"
    assert client.get(history_url).json()["total"] == 2
    assert (
        client.get(f"/api/v1/acoes/{other['id']}/atribuicoes/{row['id']}/historico").status_code
        == 404
    )
    assert client.get(f"/api/v1/acoes/{other['id']}/atribuicoes").json()["total"] == 0
    assert client.get(f"/api/v1/acoes/{first['id']}").json()["versao"] == 1
    with Session(engine) as session:
        payloads = [json.dumps(row.payload) for row in session.scalars(select(Outbox))]
        assert all(
            staff["nome"] not in payload and "profissional" not in payload for payload in payloads
        )


@pytest.mark.parametrize("scope", [[], [True], [-1], [0, 0], [2], ["0"]])
def test_invalid_assignment_scope_rejected(authenticated, scope):
    client, _, _ = authenticated
    action, staff = create(client), register(client)
    response = client.post(
        f"/api/v1/acoes/{action['id']}/atribuicoes",
        json={
            "profissional_id": staff["id"],
            "acao_versao": 1,
            "profissional_versao": 1,
            "locais_indices": scope,
        },
    )
    assert response.status_code == 422


def test_pending_inactive_stale_or_archived_assignment_rejected(authenticated):
    client, _, _ = authenticated
    action = create(client)
    staff = register(client, habilitacao_validada=False, habilitacao_referencia="")
    url = f"/api/v1/acoes/{action['id']}/atribuicoes"
    data = {"profissional_id": staff["id"], "acao_versao": 1, "profissional_versao": 1}
    assert client.post(url, json=data).status_code == 422
    assert client.post(url, json={**data, "acao_versao": 2}).status_code == 409
    updated = client.patch(
        f"/api/v1/profissionais/{staff['id']}", json={**MEDIC, "versao": 1, "ativo": False}
    )
    assert updated.status_code == 200
    assert client.post(url, json={**data, "profissional_versao": 2}).status_code == 409
    assert (
        client.request("DELETE", f"/api/v1/acoes/{action['id']}", json={"versao": 1}).status_code
        == 200
    )
    reception = client.post("/api/v1/profissionais", json=RECEPTION).json()
    assert (
        client.post(
            url, json={**data, "profissional_id": reception["id"], "acao_versao": 2}
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "change", [{"ativo": False}, {"registro_numero": "000124"}, {"habilitacao_validada": False}]
)
def test_staff_changes_revoke_assignments_with_immutable_history(authenticated, change):
    client, engine, _ = authenticated
    action, staff = create(client), register(client)
    row = assign(client, action, staff, locais_indices=[0])
    response = client.patch(
        f"/api/v1/profissionais/{staff['id']}", json={**MEDIC, "versao": 1, **change}
    )
    assert response.status_code == 200
    rows = client.get(f"/api/v1/acoes/{action['id']}/atribuicoes").json()["items"]
    assert rows[0]["ativo"] is False and rows[0]["versao"] == 2
    assert rows[0]["profissional_snapshot"]["registro_numero"] == "000123"
    with Session(engine) as session:
        history = session.scalars(
            select(StaffRevision)
            .where(StaffRevision.entidade_id == row["id"])
            .order_by(StaffRevision.versao)
        ).all()
        assert [event.dados["ativo"] for event in history] == [True, False]


def test_specific_locations_protected_and_archiving_revokes_assignments(authenticated):
    client, _, _ = authenticated
    action, staff = create(client), register(client)
    row = assign(client, action, staff, locais_indices=[0])
    url = f"/api/v1/acoes/{action['id']}"
    changed = {**ACTION, "versao": 1, "locais": list(reversed(ACTION["locais"]))}
    assert client.patch(url, json=changed).status_code == 409
    patch = {
        "versao": 1,
        "acao_versao": 1,
        "profissional_versao": 1,
        "ativo": False,
        "locais_indices": [0],
    }
    assignment_url = url + f"/atribuicoes/{row['id']}"
    assert client.patch(assignment_url, json=patch).status_code == 200
    assert client.patch(url, json=changed).status_code == 200
    assert (
        client.patch(
            assignment_url, json={**patch, "versao": 2, "acao_versao": 2, "ativo": True}
        ).status_code
        == 200
    )
    assert client.request("DELETE", url, json={"versao": 2}).status_code == 200
    assert client.get(url + "/atribuicoes").json()["items"][0]["ativo"] is False


def test_registration_never_creates_authentication_or_grants_analytics(authenticated):
    client, _, repo = authenticated
    action = create(client)
    reception = client.post("/api/v1/profissionais", json=RECEPTION).json()
    assign(client, action, reception)
    repo.professional.tipo_login = "recepcao"
    for route in [
        "/api/v1/profissionais",
        f"/api/v1/acoes/{action['id']}/atribuicoes",
        "/api/v1/indicadores",
    ]:
        assert client.get(route).status_code in {401, 403}


def test_staff_requires_session_csrf_and_restricted_verbs(api_client, authenticated):
    client, _, _ = authenticated
    client.headers.pop("X-CSRF-Token")
    assert client.post("/api/v1/profissionais", json=RECEPTION).status_code == 403
    client.cookies.clear()
    assert client.get("/api/v1/profissionais").status_code == 401
    assert client.post("/api/v1/profissionais", json=RECEPTION).status_code == 401


def test_local_staff_migration_backup_and_idempotency(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path / "old.sqlite3").as_posix())
    tables = [
        table
        for table in Base.metadata.sorted_tables
        if table
        not in {
            StaffRecord.__table__,
            StaffAssignment.__table__,
            StaffRevision.__table__,
            ClinicalRecord.__table__,
            ClinicalRevision.__table__,
        }
    ]
    Base.metadata.create_all(engine, tables=tables)
    key = Fernet.generate_key().decode()
    backup = tmp_path / "backups"
    assert not add_local_staff(engine, key, backup)
    assert not inspect(engine).has_table(StaffRecord.__tablename__)
    assert add_local_staff(engine, key, backup, apply=True)
    assert not add_local_staff(engine, key, backup, apply=True)
    assert inspect(engine).has_table(StaffAssignment.__tablename__)
    assert len(list(backup.iterdir())) == 1
    restored = sqlite3.connect(":memory:")
    restored.deserialize(Fernet(key.encode()).decrypt(next(backup.iterdir()).read_bytes()))
    assert restored.execute(
        "SELECT count(*) FROM sqlite_master WHERE name='acoes_map_profissionais'"
    ).fetchone() == (0,)
    assert restored.execute("SELECT count(*) FROM acoes_map_acoes").fetchone() == (0,)
    restored.close()
    engine.dispose()
