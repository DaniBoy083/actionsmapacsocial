import json
import sqlite3

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session
from test_actions import ACTION, create
from test_clinical import FIELDS, designate, person, setup_clinical
from test_institutional import png

from app.domain.staff import StaffInput
from app.infrastructure.models import (
    Action,
    ActionInstitution,
    Base,
    ClinicalDesignation,
    ClinicalRecord,
    Institution,
    InstitutionLogo,
    Outbox,
)
from app.infrastructure.operational_migration import TABLES, migrate_local


def metadata():
    return {
        "contratantes": [
            {"nome": "Instituição compartilhada", "tipo": "CLINICA"},
            {"nome": "Contratante dois", "tipo": "OUTRO"},
        ],
        "apoiadores": [
            {"nome": "Instituição compartilhada", "tipo": "CLINICA", "modalidade": "TOTAL"},
            {"nome": "Apoiador dois", "tipo": "ORGAO_GOVERNAMENTAL", "modalidade": "PARCIAL"},
        ],
    }


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"contratantes": []},
        {"apoiadores": []},
        {
            "contratantes": [{"nome": "Teste", "tipo": "OUTRO"}],
            "apoiadores": [{"nome": "Teste", "tipo": "OUTRO"}],
        },
        {"contratantes": [{"nome": "Teste", "tipo": "OUTRO", "modalidade": "TOTAL"}]},
    ],
)
def test_new_action_requires_roles_and_each_support_mode(authenticated, data):
    client, _, _ = authenticated
    assert client.post("/api/v1/acoes", json={**ACTION, "institucional": data}).status_code == 422
    assert client.get("/api/v1/acoes").json()["total"] == 0


def test_reusable_institutions_roles_roundtrip_filters_and_atomic_validation(authenticated):
    client, engine, _ = authenticated
    original = create(client, institucional=metadata())
    url = f"/api/v1/acoes/{original['id']}"
    data = original["institucional"]
    assert data["contratantes"][0]["instituicao_id"] == data["apoiadores"][0]["instituicao_id"]
    other = create(client, institucional=data)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Institution)) == 3
        assert session.scalar(select(func.count()).select_from(ActionInstitution)) == 8
    changed = {
        **data,
        "contratantes": [data["contratantes"][1]],
        "apoiadores": list(reversed(data["apoiadores"])),
    }
    saved = client.patch(url, json={**ACTION, "versao": 1, "institucional": changed})
    assert saved.status_code == 200, saved.text
    assert client.get(url).json()["institucional"] == saved.json()["institucional"]
    assert client.get(url + "/institucional/versoes/1").json()["institucional"] == data
    assert (
        client.get(
            "/api/v1/acoes", params={"contratante": "Contratante dois", "apoio": "TOTAL"}
        ).json()["total"]
        == 2
    )
    assert (
        client.get("/api/v1/indicadores", params={"apoiador": "Apoiador dois"}).json()["acoes"] == 2
    )
    assert client.get("/api/v1/acoes", params={"clinica": "compartilhada"}).json()["total"] == 2
    invalid = {**changed, "apoiadores": changed["apoiadores"] * 2}
    assert (
        client.patch(url, json={**ACTION, "versao": 2, "institucional": invalid}).status_code == 422
    )
    assert client.get(url).json()["versao"] == 2
    assert client.get(f"/api/v1/acoes/{other['id']}").json()["institucional"] == data


def test_search_normalized_aliases_explicit_logo_reuse_and_cross_institution_denied(authenticated):
    client, engine, _ = authenticated
    inst = client.post(
        "/api/v1/instituicoes",
        json={
            "nome": "Órgão de Teste",
            "tipo": "ORGAO_GOVERNAMENTAL",
            "aliases": ["Sigla Sintética"],
        },
    ).json()
    assert (
        client.post(
            "/api/v1/instituicoes", json={"nome": "orgao de teste", "tipo": "ORGAO_GOVERNAMENTAL"}
        ).json()["id"]
        == inst["id"]
    )
    result = client.get("/api/v1/instituicoes", params={"busca": "sigla sintetica"}).json()
    assert result["items"][0]["correspondencia"] == "EXATA"
    assert result["fonte_externa_habilitada"] is False
    assert client.get("/api/v1/instituicoes", params={"busca": "%"}).json()["items"] == []
    data = metadata()
    data["apoiadores"][0].update(uso_autorizado=True, conteudo_base64=png())
    action = create(client, institucional=data)
    brand = action["institucional"]["apoiadores"][0]
    endpoint = f"/api/v1/instituicoes/{brand['instituicao_id']}/marcas/{brand['logo_id']}"
    image = client.get(endpoint)
    assert image.status_code == 200 and b"TRAILING_PRIVATE_METADATA" not in image.content
    assert image.headers["cache-control"] == "no-store"
    found = client.get(
        "/api/v1/instituicoes", params={"busca": "Instituicao compartilhada"}
    ).json()["items"][0]
    assert found["logo_id"] == brand["logo_id"] and found["origem"] == "UPLOAD_INSTITUCIONAL"
    reused = create(client, institucional=action["institucional"])
    assert reused["institucional"]["apoiadores"][0]["logo_id"] == brand["logo_id"]
    wrong = metadata()
    wrong["apoiadores"][1].update(uso_autorizado=True, logo_id=brand["logo_id"])
    assert client.post("/api/v1/acoes", json={**ACTION, "institucional": wrong}).status_code == 422
    assert client.get(endpoint.replace(brand["instituicao_id"], inst["id"])).status_code == 404
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(InstitutionLogo)) == 1
        for row in session.scalars(select(Outbox)):
            assert "compartilhada" not in json.dumps(
                row.payload
            ) and "instituicao_id" not in json.dumps(row.payload)


def test_historical_empty_metadata_survives_without_inventing_roles(authenticated):
    client, engine, repo = authenticated
    with Session(engine) as session, session.begin():
        row = Action(
            nome="Legado sintético",
            locais=ACTION["locais"],
            criado_por=repo.professional.profissional_id,
            institucional={"apoio": "TOTAL", "governo": {"nome": "Parceiro legado"}},
        )
        session.add(row)
        session.flush()
        identifier = row.id
    url = f"/api/v1/acoes/{identifier}"
    before = client.get(url).json()["institucional"]
    assert before["contratantes"] == before["apoiadores"] == []
    after = client.patch(url, json={**ACTION, "versao": 1})
    assert after.status_code == 200 and after.json()["institucional"] == before


def test_support_filter_uses_current_supporters_before_legacy_global_mode(authenticated):
    client, _, _ = authenticated
    data = metadata()
    data["apoio"] = "TOTAL"
    for link in data["apoiadores"]:
        link["modalidade"] = "PARCIAL"
    create(client, institucional=data)
    assert client.get("/api/v1/acoes", params={"apoio": "TOTAL"}).json()["total"] == 0
    assert client.get("/api/v1/acoes", params={"apoio": "PARCIAL"}).json()["total"] == 1


def test_case_must_be_designated_even_before_first_record_and_revocation_is_immediate(
    authenticated, monkeypatch
):
    client, _, _, action, staff, _, assigned = setup_clinical(authenticated, monkeypatch)
    unassigned = person(client, action["id"], name="Pessoa sintética ainda não designada")
    endpoint = f"/api/v1/acoes/{action['id']}/beneficiarios/{unassigned}/clinica"
    assert client.get(endpoint).status_code == 403
    assert client.put(endpoint, json={"campos": FIELDS}).status_code == 403
    designate(client, action["id"], unassigned, staff["id"])
    assert client.put(endpoint, json={"campos": FIELDS}).status_code == 200
    assignment = endpoint.removesuffix("clinica") + "designacao-clinica"
    assert (
        client.put(assignment, json={"profissional_id": staff["id"], "versao": 0}).status_code
        == 409
    )
    assert (
        client.put(
            assignment, json={"profissional_id": staff["id"], "versao": 1, "ativo": False}
        ).status_code
        == 200
    )
    assert client.get(endpoint, params={"versao": 1}).status_code == 403
    assert client.get(endpoint.replace(unassigned, assigned)).status_code == 200
    client.headers.pop("X-CSRF-Token")
    assert (
        client.put(assignment, json={"profissional_id": staff["id"], "versao": 2}).status_code
        == 403
    )


@pytest.mark.parametrize("route", ["/api/v1/instituicoes", "/api/v1/indicadores", "/api/v1/acoes"])
def test_operational_identity_is_still_closed_pending_validated_auth(authenticated, route):
    client, _, repo = authenticated
    repo.professional.tipo_login = "recepcao"
    assert client.get(route).status_code == 403


def test_optometrist_requires_accepted_registration_reception_has_no_clinical_fields():
    with pytest.raises(ValueError):
        StaffInput(nome="Teste sintético", categoria="OPTOMETRISTA")
    assert StaffInput(nome="Teste sintético", categoria="RECEPCAO").registro_numero is None
    assert (
        StaffInput(
            nome="Teste sintético",
            categoria="OPTOMETRISTA",
            registro_conselho="ÓRGÃO SINTÉTICO",
            registro_numero="0001",
            registro_uf="PB",
        ).registro_conselho
        != "CRM"
    )


def test_sql_pagination_has_constant_query_count_and_correct_territorial_filter(authenticated):
    client, engine, _ = authenticated
    for _ in range(12):
        create(client)
    statements = []

    def collect(*_):
        statements.append(1)

    event.listen(engine, "before_cursor_execute", collect)
    try:
        small = client.get("/api/v1/acoes", params={"tamanho": 1})
        first = len(statements)
        statements.clear()
        large = client.get(
            "/api/v1/acoes", params={"tamanho": 10, "municipio": "2504009", "pagina": 2}
        )
        assert len(statements) == first
        assert small.json()["total"] == large.json()["total"] == 12
        assert len(large.json()["items"]) == 2
    finally:
        event.remove(engine, "before_cursor_execute", collect)


def test_migration_backup_restore_backfill_and_idempotence(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path / "legacy.sqlite3").as_posix())
    Base.metadata.create_all(
        engine, tables=[t for t in Base.metadata.sorted_tables if t not in TABLES]
    )
    # Somente metadados sintéticos: não é uma ficha clínica de produção.
    with Session(engine) as session, session.begin():
        session.add(
            ClinicalRecord(
                id="record",
                participacao_id="synthetic-participation",
                autor_profissional_id="synthetic-staff",
                autor_identidade_id="synthetic-identity",
                dados_cifrados="opaque-synthetic",
                contexto={},
            )
        )
    key = Fernet.generate_key().decode()
    backups = tmp_path / "backups"
    assert not migrate_local(engine, key, backups)["aplicado"]
    assert not backups.exists()
    result = migrate_local(engine, key, backups, apply=True)
    assert result == {"tabelas_pendentes": 4, "designacoes_pendentes": 1, "aplicado": True}
    assert not migrate_local(engine, key, backups, apply=True)["aplicado"]
    with Session(engine) as session:
        assert (
            session.get(ClinicalDesignation, "synthetic-participation").identidade_id
            == "synthetic-identity"
        )
        assert session.get(ClinicalRecord, "record").dados_cifrados == "opaque-synthetic"
    restored = sqlite3.connect(":memory:")
    restored.deserialize(Fernet(key.encode()).decrypt(next(backups.iterdir()).read_bytes()))
    assert restored.execute("SELECT count(*) FROM acoes_map_fichas_clinicas").fetchone()[0] == 1
    assert not restored.execute(
        "SELECT 1 FROM sqlite_master WHERE name='acoes_map_designacoes_clinicas'"
    ).fetchone()
    restored.close()
    engine.dispose()
