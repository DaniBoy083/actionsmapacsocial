import base64
import io
import json
import sqlite3

import pytest
from app.infrastructure.local_migrations import add_local_institutional_metadata
from app.infrastructure.models import ActionLogo, Base, InstitutionalRevision, Outbox, Participation
from cryptography.fernet import Fernet
from PIL import Image
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.orm import Session
from test_actions import ACTION, create


def png(size=(96, 96)):
    output = io.BytesIO()
    Image.new("RGB", size, "red").save(output, "PNG")
    return base64.b64encode(output.getvalue() + b"TRAILING_PRIVATE_METADATA").decode()


def institutional(support="TOTAL"):
    return {
        "apoio": support,
        "instrumento": {
            "tipo": "EMENDA",
            "nome": "Instrumento sintético",
            "numero": "0007/2026",
            "autor": "Autor institucional sintético",
            "divulgacao_autorizada": True,
        },
        "governo": {
            "nome": "Órgão sintético",
            "uso_autorizado": True,
            "divulgacao_autorizada": False,
            "conteudo_base64": png(),
        },
        "clinica": {
            "nome": "Clínica sintética",
            "uso_autorizado": True,
            "divulgacao_autorizada": True,
            "conteudo_base64": png(),
        },
    }


@pytest.mark.parametrize("support", [None, "TOTAL", "PARCIAL"])
def test_three_brand_slots_and_private_sanitized_assets(authenticated, support):
    client, engine, _ = authenticated
    action = create(client, institucional=institutional(support))
    data = action["institucional"]
    assert data["apoio"] == support
    assert data["instrumento"]["numero"] == "0007/2026"
    assert "conteudo_base64" not in json.dumps(data)
    for slot in ("governo", "clinica"):
        logo_id = data[slot]["logo_id"]
        response = client.get(f"/api/v1/acoes/{action['id']}/marcas/{logo_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers["cache-control"] == "no-store"
        assert b"TRAILING_PRIVATE_METADATA" not in response.content
        with Image.open(io.BytesIO(response.content)) as image:
            assert image.size == (96, 96)
            assert not image.info
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ActionLogo)) == 2
        assert session.get(InstitutionalRevision, (action["id"], 1)).dados == data
        for row in session.scalars(select(Outbox)):
            payload = json.dumps(row.payload)
            assert row.payload["schema_version"] == "1.1"
            assert "institucional" not in payload
            assert "Instrumento sint" not in payload
            assert "logo_id" not in payload


def test_absent_partners_and_legacy_edits_preserve_metadata(authenticated):
    client, _, _ = authenticated
    empty = create(client)
    assert empty["institucional"]["apoio"] is None
    assert empty["institucional"]["governo"]["logo_id"] is None
    action = create(client, institucional=institutional())
    url = f"/api/v1/acoes/{action['id']}"
    response = client.patch(url, json={**ACTION, "nome": "Editada", "versao": 1})
    assert response.status_code == 200
    assert response.json()["institucional"] == action["institucional"]
    assert client.patch(url, json={**ACTION, "versao": 1}).status_code == 409


@pytest.mark.parametrize(
    "change",
    [
        {"apoio": "INVENTADO"},
        {"instrumento": {"nome": "Sem tipo"}},
        {"instrumento": {"tipo": "EMENDA", "divulgacao_autorizada": True}},
        {"governo": {"nome": "Órgão", "conteudo_base64": png()}},
        {"clinica": {"nome": "Clínica", "divulgacao_autorizada": True}},
        {"governo": {"nome": "Órgão", "uso_autorizado": "sim"}},
        {"cpf_paciente": "PRIVATE_SENTINEL"},
    ],
)
def test_institutional_validation(authenticated, change):
    client, _, _ = authenticated
    response = client.post("/api/v1/acoes", json={**ACTION, "institucional": change})
    assert response.status_code == 422
    assert "PRIVATE_SENTINEL" not in response.text


@pytest.mark.parametrize(
    "content",
    [
        "bad-base64",
        base64.b64encode(b"<svg onload='alert(1)'/>").decode(),
        png((16, 16)),
        png((2049, 64)),
    ],
)
def test_invalid_logos_rollback_action_and_outbox(authenticated, content):
    client, engine, _ = authenticated
    data = institutional()
    data["governo"]["conteudo_base64"] = content
    response = client.post("/api/v1/acoes", json={**ACTION, "institucional": data})
    assert response.status_code == 422
    assert client.get("/api/v1/acoes").json()["total"] == 0
    with Session(engine) as session:
        assert not session.scalar(select(ActionLogo))
        assert not session.scalar(select(Outbox))


def test_assets_cannot_cross_action_or_slot(authenticated):
    client, _, _ = authenticated
    first = create(client, institucional=institutional())
    other = create(client)
    logo = first["institucional"]["governo"]["logo_id"]
    assert client.get(f"/api/v1/acoes/{other['id']}/marcas/{logo}").status_code == 404
    for action_id, slot in [(other["id"], "governo"), (first["id"], "clinica")]:
        response = client.patch(
            f"/api/v1/acoes/{action_id}",
            json={
                **ACTION,
                "versao": 1,
                "institucional": {
                    slot: {
                        "nome": "Teste",
                        "uso_autorizado": True,
                        "logo_id": logo,
                    }
                },
            },
        )
        assert response.status_code == 422


def test_institutional_revision_and_receipt_snapshot_survive_edits(authenticated):
    client, engine, _ = authenticated
    action = create(client, institucional=institutional())
    url = f"/api/v1/acoes/{action['id']}"
    client.post(url + "/beneficiarios", json={"nome": "Pessoa Sintética"})
    person_id = client.get(url + "/beneficiarios").json()["items"][0]["id"]
    receipt = url + f"/beneficiarios/{person_id}/segunda-via"
    issued = client.get(receipt).json()
    assert issued["acao"]["institucional"] == action["institucional"]
    changed = client.patch(
        url, json={**ACTION, "nome": "Nova identificação", "versao": 2, "institucional": {}}
    )
    assert changed.status_code == 200
    assert changed.json()["institucional"]["governo"]["logo_id"] is None
    again = client.get(receipt).json()
    assert again["acao"] == issued["acao"]
    current = client.get(url + f"/beneficiarios/{person_id}").json()
    assert current["acao"]["nome"] == "Nova identificação"
    old = client.get(url + "/institucional/versoes/1")
    assert old.status_code == 200
    assert old.json()["institucional"] == action["institucional"]
    old_logo = action["institucional"]["governo"]["logo_id"]
    assert client.get(url + f"/marcas/{old_logo}").status_code == 200
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Participation)) == 1


@pytest.mark.parametrize("team", ["administracao", "tecnologia"])
def test_existing_institutional_teams_can_manage_metadata(authenticated, team):
    client, _, repo = authenticated
    repo.professional.equipe = team
    assert (
        client.post("/api/v1/acoes", json={**ACTION, "institucional": institutional()}).status_code
        == 201
    )


@pytest.mark.parametrize("role", ["recepcao", "profissional"])
def test_unvalidated_operational_profiles_denied(authenticated, role):
    client, _, repo = authenticated
    action = create(client, institucional=institutional())
    repo.professional.tipo_login = role
    url = f"/api/v1/acoes/{action['id']}"
    for endpoint in [
        url,
        url + "/marcas/" + action["institucional"]["governo"]["logo_id"],
        url + "/institucional/versoes/1",
        "/api/v1/indicadores",
    ]:
        assert client.get(endpoint).status_code in {401, 403}


def test_assets_and_metadata_require_session_and_csrf(api_client):
    client, _, _ = api_client
    assert (
        client.post("/api/v1/acoes", json={**ACTION, "institucional": institutional()}).status_code
        == 401
    )
    assert client.get("/api/v1/acoes/synthetic/marcas/synthetic").status_code == 401


def test_institutional_changes_require_csrf(authenticated):
    client, _, _ = authenticated
    client.headers.pop("X-CSRF-Token")
    assert (
        client.post("/api/v1/acoes", json={**ACTION, "institucional": institutional()}).status_code
        == 403
    )


def test_filters_count_only_matching_venues_and_show_missing_data(authenticated):
    client, _, _ = authenticated
    first = create(client, institucional=institutional(), inicio_em="2026-11-10")
    url = f"/api/v1/acoes/{first['id']}"
    client.post(url + "/beneficiarios", json={"nome": "Pessoa A", "local_indice": 0})
    client.post(url + "/beneficiarios", json={"nome": "Pessoa B", "local_indice": 1})
    client.post(url + "/beneficiarios", json={"nome": "Pessoa sem local"})
    create(client)
    filtered = client.get(
        "/api/v1/acoes", params={"numero_instrumento": "0007", "autor": "sintético"}
    ).json()
    assert filtered["total"] == 1
    assert client.get("/api/v1/acoes", params={"autor": "%"}).json()["total"] == 0
    result = client.get(
        "/api/v1/indicadores",
        params={"acao": first["id"], "municipio": "2507507", "autor": "sintético"},
    ).json()
    assert (
        result["acoes"]
        == result["municipios"]
        == result["participacoes"]
        == result["cadastros_distintos"]
        == 1
    )
    assert result["participacoes_sem_local"] == 1
    assert len(result["por_municipio"]) == 1
    result = client.get("/api/v1/indicadores", params={"apoio": "TOTAL"}).json()
    assert result["acoes"] == 1 and result["participacoes"] == 3
    assert client.get("/api/v1/indicadores").json()["acoes_sem_instrumento"] == 1
    assert client.get("/api/v1/indicadores", params={"inicio": "2026-11-11"}).json()["acoes"] == 0
    assert (
        client.get(
            "/api/v1/indicadores", params={"inicio": "2026-11-10", "fim": "2026-11-10"}
        ).json()["acoes"]
        == 1
    )
    assert client.get("/api/v1/indicadores", params={"municipio": "INVALID"}).status_code == 422
    assert (
        client.get(
            "/api/v1/indicadores", params={"inicio": "2026-11-11", "fim": "2026-11-10"}
        ).status_code
        == 422
    )


def test_local_migration_backup_preservation_and_idempotency(tmp_path):
    database = tmp_path / "legacy.sqlite3"
    engine = create_engine("sqlite:///" + database.as_posix())
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE acoes_map_acoes DROP COLUMN institucional"))
        connection.execute(
            text("ALTER TABLE acoes_map_participacoes DROP COLUMN documento_institucional")
        )
        connection.execute(
            text(
                "INSERT INTO acoes_map_acoes (id,versao,nome,categoria,descricao,resumo_publico,status,locais,criado_por,criado_em,atualizado_em) VALUES ('synthetic',1,'Preservada','','','','em_revisao','[]','test','2026-11-11','2026-11-11')"
            )
        )
    key = Fernet.generate_key().decode()
    backup = tmp_path / "backup"
    assert not add_local_institutional_metadata(engine, key, backup)
    assert "institucional" not in {
        c["name"] for c in inspect(engine).get_columns("acoes_map_acoes")
    }
    assert add_local_institutional_metadata(engine, key, backup, apply=True)
    assert not add_local_institutional_metadata(engine, key, backup, apply=True)
    assert len(list(backup.iterdir())) == 1
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT nome FROM acoes_map_acoes")) == "Preservada"
        assert connection.scalar(text("SELECT institucional FROM acoes_map_acoes")) == "{}"
    restored = sqlite3.connect(":memory:")
    restored.deserialize(Fernet(key.encode()).decrypt(next(backup.iterdir()).read_bytes()))
    assert restored.execute("SELECT nome FROM acoes_map_acoes").fetchone() == ("Preservada",)
    assert "institucional" not in {
        c[1] for c in restored.execute("PRAGMA table_info(acoes_map_acoes)")
    }
    restored.close()
    engine.dispose()
