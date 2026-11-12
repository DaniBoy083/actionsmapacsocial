import json

import pytest
from conftest import PASSWORD
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session
from test_actions import ACTION, create
from test_staff import MEDIC, assign, register

from app.config import get_settings
from app.infrastructure.local_migrations import add_local_clinical
from app.infrastructure.models import Base, ClinicalRecord, ClinicalRevision, Outbox

FIELDS = {
    "glicose": "",
    "pressao": "valor sintético",
    "tipo_sangue": None,
    "od": {"esferico": "-1,25", "cilindrico": None, "eixo": "teste", "dp": "sem unidade presumida"},
    "oe": {},
    "adicao": None,
    "lentes": "MARCADOR_CLINICO_SINTETICO",
}


def enable(monkeypatch):
    monkeypatch.setenv("CLINICAL_FIELDS_ENABLED", "true")
    get_settings.cache_clear()


def eligible(client, repo, **changes):
    return register(
        client,
        identidade_institucional_id=repo.professional.profissional_id,
        registro_clinico_autorizado=True,
        autorizacao_clinica_referencia="Autorização clínica sintética",
        **changes,
    )


def person(client, action_id, local=0, name="Pessoa clínica sintética"):
    url = f"/api/v1/acoes/{action_id}"
    assert (
        client.post(url + "/beneficiarios", json={"nome": name, "local_indice": local}).status_code
        == 201
    )
    return next(
        row["id"]
        for row in client.get(url + "/beneficiarios").json()["items"]
        if row["nome"] == name
    )


def setup_clinical(authenticated, monkeypatch, scope=None):
    client, engine, repo = authenticated
    enable(monkeypatch)
    action = create(client)
    person_id = person(client, action["id"])
    action = client.get(f"/api/v1/acoes/{action['id']}").json()
    staff = eligible(client, repo)
    assignment = assign(client, action, staff, locais_indices=scope)
    designate(client, action["id"], person_id, staff["id"])
    return client, engine, repo, action, staff, assignment, person_id


def designate(client, action_id, person_id, staff_id):
    response = client.put(
        f"/api/v1/acoes/{action_id}/beneficiarios/{person_id}/designacao-clinica",
        json={"profissional_id": staff_id},
    )
    assert response.status_code == 200, response.text


def test_clinical_fields_encrypted_versioned_and_not_exported(authenticated, monkeypatch):
    client, engine, _, action, _, _, person_id = setup_clinical(authenticated, monkeypatch)
    url = f"/api/v1/acoes/{action['id']}/beneficiarios/{person_id}/clinica"
    assert client.get(f"/api/v1/acoes/{action['id']}/acesso-clinico").json() == {"permitido": True}
    draft = client.get(url)
    assert draft.status_code == 200 and draft.json()["versao"] == 0
    first = client.put(url, json={"versao": 0, "campos": FIELDS})
    assert first.status_code == 200, first.text
    assert first.json()["campos"]["glicose"] is None
    assert first.json()["campos"]["od"]["esferico"] == "-1,25"
    assert first.json()["estado"] == "EM_PREENCHIMENTO"
    assert first.headers["cache-control"] == "no-store"
    assert client.put(url, json={"versao": 0, "campos": FIELDS}).status_code == 409
    assert (
        client.put(
            url, json={"versao": 1, "campos": {**FIELDS, "adicao": "revisão sintética"}}
        ).status_code
        == 200
    )
    old = client.get(url, params={"versao": 1}).json()
    assert old["campos"]["adicao"] is None
    assert client.get(url).json()["campos"]["adicao"] == "revisão sintética"
    general = client.get(url.removesuffix("/clinica")).json()
    assert "MARCADOR_CLINICO_SINTETICO" not in json.dumps(general)
    assert client.get(f"/api/v1/acoes/{action['id']}").json()["versao"] == action["versao"]
    with Session(engine) as session:
        record = session.scalar(select(ClinicalRecord))
        assert "MARCADOR_CLINICO_SINTETICO" not in record.dados_cifrados
        assert "lentes" not in record.dados_cifrados
        assert len(session.scalars(select(ClinicalRevision)).all()) == 2
        for event in session.scalars(select(Outbox)):
            payload = json.dumps(event.payload)
            assert "MARCADOR_CLINICO_SINTETICO" not in payload and "clinica" not in payload


@pytest.mark.parametrize(
    "field,value",
    [
        ("diagnostico", "PRIVATE_SENTINEL"),
        ("glicose", 120),
        ("od", {"dnp": "PRIVATE_SENTINEL"}),
        ("lentes", "x" * 161),
    ],
)
def test_clinical_schema_exact_optional_and_no_value_echo(authenticated, monkeypatch, field, value):
    client, _, _, action, _, _, person_id = setup_clinical(authenticated, monkeypatch)
    url = f"/api/v1/acoes/{action['id']}/beneficiarios/{person_id}/clinica"
    response = client.put(url, json={"campos": {**FIELDS, field: value}, "versao": 0})
    assert response.status_code == 422
    assert "PRIVATE_SENTINEL" not in response.text


def test_clinical_feature_defaults_closed_and_requires_separate_key(authenticated, monkeypatch):
    client, _, _, action, _, _, person_id = setup_clinical(authenticated, monkeypatch)
    url = f"/api/v1/acoes/{action['id']}/beneficiarios/{person_id}/clinica"
    for enabled, key in [
        ("false", Fernet.generate_key().decode()),
        ("true", ""),
        ("true", get_settings().beneficiaries_key.get_secret_value()),
    ]:
        monkeypatch.setenv("CLINICAL_FIELDS_ENABLED", enabled)
        monkeypatch.setenv("CLINICAL_KEY", key)
        get_settings.cache_clear()
        assert client.get(url).status_code == 503
        assert client.get(f"/api/v1/acoes/{action['id']}/acesso-clinico").json() == {
            "permitido": False
        }


def test_clinical_permission_not_granted_by_admin_role_registration_or_assignment_alone(
    authenticated, monkeypatch
):
    client, _, repo = authenticated
    enable(monkeypatch)
    action = create(client)
    person_id = person(client, action["id"])
    action = client.get(f"/api/v1/acoes/{action['id']}").json()
    url = f"/api/v1/acoes/{action['id']}/beneficiarios/{person_id}/clinica"
    assert client.get(url).status_code == 403
    staff = register(client, identidade_institucional_id=repo.professional.profissional_id)
    assign(client, action, staff)
    assert client.get(url).status_code == 403
    assert client.put(url, json={"campos": FIELDS}).status_code == 403


def test_clinical_local_scope_and_revocation_enforced_each_request(authenticated, monkeypatch):
    client, _, _, action, staff, _assignment, person_id = setup_clinical(
        authenticated, monkeypatch, scope=[0]
    )
    other = person(client, action["id"], local=1, name="Outra pessoa sintética")
    url = f"/api/v1/acoes/{action['id']}/beneficiarios/{person_id}/clinica"
    assert client.get(url.replace(person_id, other)).status_code == 404
    assert client.put(url, json={"campos": FIELDS}).status_code == 200
    assert (
        client.patch(
            f"/api/v1/profissionais/{staff['id']}", json={**MEDIC, "versao": 1, "ativo": False}
        ).status_code
        == 200
    )
    assert client.get(url).status_code == 403
    assert client.get(url, params={"versao": 1}).status_code == 403
    assert client.put(url, json={"campos": FIELDS, "versao": 1}).status_code == 403


def login_as(client, repo, identity):
    client.cookies.clear()
    repo.professional.profissional_id = identity
    assert (
        client.post(
            "/api/v1/auth/login", json={"identifier": "test@example.invalid", "password": PASSWORD}
        ).status_code
        == 204
    )
    client.headers["X-CSRF-Token"] = client.get("/api/v1/auth/me").json()["csrf_token"]


def test_other_professional_cannot_read_or_overwrite_claimed_case(authenticated, monkeypatch):
    client, _, repo, action, _, _, person_id = setup_clinical(authenticated, monkeypatch)
    url = f"/api/v1/acoes/{action['id']}/beneficiarios/{person_id}/clinica"
    assert client.put(url, json={"campos": FIELDS}).status_code == 200
    login_as(client, repo, "other-synthetic-professional")
    other = eligible(client, repo, registro_numero="456")
    assign(client, action, other)
    assert client.get(url).status_code == 403
    assert client.get(url, params={"versao": 1}).status_code == 403
    assert client.put(url, json={"campos": FIELDS, "versao": 1}).status_code == 403


def test_clinical_context_preserved_and_ciphertext_bound_to_case(authenticated, monkeypatch):
    client, engine, _, action, staff, _, person_id = setup_clinical(authenticated, monkeypatch)
    url = f"/api/v1/acoes/{action['id']}/beneficiarios/{person_id}/clinica"
    first = client.put(url, json={"campos": FIELDS}).json()
    assert (
        client.patch(
            f"/api/v1/acoes/{action['id']}",
            json={**ACTION, "nome": "Ação renomeada", "versao": action["versao"]},
        ).status_code
        == 200
    )
    assert client.get(url).json()["contexto"] == first["contexto"]
    another = person(client, action["id"], name="Pessoa de outro registro")
    designate(client, action["id"], another, staff["id"])
    assert client.put(url.replace(person_id, another), json={"campos": FIELDS}).status_code == 200
    with Session(engine) as session, session.begin():
        original = session.get(ClinicalRecord, first["id"])
        other_record = session.scalar(
            select(ClinicalRecord).where(ClinicalRecord.id != first["id"])
        )
        original.dados_cifrados = other_record.dados_cifrados
    response = client.get(url)
    assert response.status_code == 503
    assert "MARCADOR_CLINICO_SINTETICO" not in response.text


def test_clinical_csrf_and_session_required(authenticated, monkeypatch):
    client, _, _, action, _, _, person_id = setup_clinical(authenticated, monkeypatch)
    url = f"/api/v1/acoes/{action['id']}/beneficiarios/{person_id}/clinica"
    client.headers.pop("X-CSRF-Token")
    assert client.put(url, json={"campos": FIELDS}).status_code == 403
    client.cookies.clear()
    assert client.get(url).status_code == 401


def test_rebinding_same_staff_record_does_not_transfer_existing_case(authenticated, monkeypatch):
    client, _, repo, action, staff, assignment, person_id = setup_clinical(
        authenticated, monkeypatch
    )
    url = f"/api/v1/acoes/{action['id']}/beneficiarios/{person_id}/clinica"
    assert client.put(url, json={"campos": FIELDS}).status_code == 200
    profile_url = f"/api/v1/profissionais/{staff['id']}"
    profile = {
        key: value
        for key, value in staff.items()
        if key
        in {
            **MEDIC,
            "identidade_institucional_id": None,
            "registro_clinico_autorizado": None,
            "autorizacao_clinica_referencia": None,
        }
    }
    assert (
        client.patch(
            profile_url, json={**profile, "versao": 1, "identidade_institucional_id": None}
        ).status_code
        == 200
    )
    login_as(client, repo, "new-holder-of-staff-record")
    assert (
        client.patch(
            profile_url,
            json={
                **profile,
                "versao": 2,
                "identidade_institucional_id": repo.professional.profissional_id,
            },
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/acoes/{action['id']}/atribuicoes/{assignment['id']}",
            json={
                "versao": 2,
                "acao_versao": action["versao"],
                "profissional_versao": 3,
                "ativo": True,
            },
        ).status_code
        == 200
    )
    assert client.get(f"/api/v1/acoes/{action['id']}/acesso-clinico").json()["permitido"]
    assert client.get(url).status_code == 403
    assert client.get(url, params={"versao": 1}).status_code == 403


def test_cannot_bind_another_identity_or_grant_reception_clinical_capability(authenticated):
    client, _, _ = authenticated
    assert (
        client.post(
            "/api/v1/profissionais",
            json={**MEDIC, "identidade_institucional_id": "another-identity"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/profissionais",
            json={
                "nome": "Recepção sintética",
                "categoria": "RECEPCAO",
                "registro_clinico_autorizado": True,
                "autorizacao_clinica_referencia": "Teste",
            },
        ).status_code
        == 422
    )


def test_local_clinical_migration_is_additive_and_does_not_enable_feature(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path / "old.sqlite3").as_posix())
    Base.metadata.create_all(
        engine,
        tables=[
            table
            for table in Base.metadata.sorted_tables
            if table not in {ClinicalRecord.__table__, ClinicalRevision.__table__}
        ],
    )
    key = Fernet.generate_key().decode()
    assert not add_local_clinical(engine, key, tmp_path / "backup")
    assert add_local_clinical(engine, key, tmp_path / "backup", apply=True)
    assert not add_local_clinical(engine, key, tmp_path / "backup", apply=True)
    assert inspect(engine).has_table(ClinicalRecord.__tablename__)
    assert len(list((tmp_path / "backup").iterdir())) == 1
    engine.dispose()
