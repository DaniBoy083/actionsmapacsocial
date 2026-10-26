import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest
from app.domain.contracts import ActionInput
from app.domain.integrations import CredentialInput
from app.infrastructure.actions import change_status, save_action
from app.infrastructure.integrations import SqlCredentialRepository
from app.infrastructure.models import Audit, IntegrationCredential, IntegrationExport
from conftest import PASSWORD
from sqlalchemy import MetaData, create_engine, func, inspect, select
from sqlalchemy.orm import Session
from test_actions import create

BASE = "/api/v1/tecnologia/tokens"
EXPORT = "/api/v1/integracoes/acoes/resumos"


def issue(client):
    response = client.post(
        BASE, json={"nome": "Agenda sintética", "password": PASSWORD, "validade_dias": 30}
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_token_one_time_hashed_scoped_and_revocable(authenticated):
    client, engine, _ = authenticated
    issued = issue(client)
    raw = issued["token"]
    identifier = issued["credencial"]["id"]
    listing = client.get(BASE)
    assert (
        raw not in listing.text
        and "token_hash" not in listing.text
        and PASSWORD not in listing.text
    )
    assert listing.headers["cache-control"] == "no-store"
    assert listing.json()[0]["escopo"] == "acoes.resumos.read"
    with Session(engine) as session:
        row = session.get(IntegrationCredential, identifier)
        assert row.token_hash == hashlib.sha256(raw.encode()).hexdigest()
        assert raw not in str(row.__dict__)
    authorization = {"Authorization": "Bearer " + raw}
    assert (
        client.get("/api/v1/integracoes/health").status_code == 401
    )  # Cookie não é credencial de serviço.
    assert client.get("/api/v1/integracoes/health", headers=authorization).status_code == 200
    assert client.get("/api/v1/acoes", headers={**authorization, "Cookie": ""}).status_code == 401
    assert client.get(BASE, headers={**authorization, "Cookie": ""}).status_code == 401
    assert (
        client.post(BASE + f"/{identifier}/revogar", json={"password": PASSWORD}).status_code == 200
    )
    assert client.get("/api/v1/integracoes/health", headers=authorization).status_code == 401
    with Session(engine) as session:
        operations = list(session.scalars(select(Audit.operacao)))
        assert "integracoes.token.create" in operations and "integracoes.token.revoke" in operations


def test_credential_management_requires_role_origin_csrf_and_password(authenticated):
    client, engine, repo = authenticated
    body = {"nome": "Agenda sintética", "password": PASSWORD}
    assert client.post(BASE, json=body, headers={"X-CSRF-Token": ""}).status_code == 403
    assert (
        client.post(
            BASE, json=body, headers={"Origin": "https://untrusted.example.invalid"}
        ).status_code
        == 403
    )
    assert client.post(BASE, json={**body, "password": "incorrect-synthetic"}).status_code == 401
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(IntegrationCredential)) == 0
    repo.professional.equipe = "administracao"
    assert client.get(BASE).status_code == 403
    assert client.post(BASE, json=body).status_code == 403


def test_rotation_atomic_and_expiration_enforced(authenticated):
    client, engine, _ = authenticated
    previous = issue(client)
    identifier = previous["credencial"]["id"]
    assert (
        client.post(
            BASE + f"/{identifier}/rotacionar", json={"nome": "Substituto", "password": "bad"}
        ).status_code
        == 401
    )
    assert (
        client.get(
            "/api/v1/integracoes/health", headers={"Authorization": "Bearer " + previous["token"]}
        ).status_code
        == 200
    )
    rotated = client.post(
        BASE + f"/{identifier}/rotacionar", json={"nome": "Substituto", "password": PASSWORD}
    ).json()
    assert rotated["token"] != previous["token"]
    assert (
        client.get(
            "/api/v1/integracoes/health", headers={"Authorization": "Bearer " + previous["token"]}
        ).status_code
        == 401
    )
    with Session(engine) as session, session.begin():
        session.get(IntegrationCredential, rotated["credencial"]["id"]).expira_em = datetime.now(
            UTC
        ) - timedelta(seconds=1)
    assert (
        client.get(
            "/api/v1/integracoes/health", headers={"Authorization": "Bearer " + rotated["token"]}
        ).status_code
        == 401
    )


def test_frozen_export_keeps_pages_and_retracts_with_new_snapshot(authenticated):
    client, engine, _ = authenticated
    row = create(client)
    issued = issue(client)
    headers = {"Authorization": "Bearer " + issued["token"]}
    first = client.get(EXPORT, headers=headers)
    assert first.status_code == 200, first.text
    frozen = first.json()
    assert frozen["total_itens"] == 1 and frozen["quantidade_acoes"] == 0
    item = frozen["items"][0]
    assert item["acao_id"] == row["id"] and item["publicavel"] is False
    assert "nome" not in item and "beneficiario_id" not in json.dumps(item)
    assert (
        client.request("DELETE", f"/api/v1/acoes/{row['id']}", json={"versao": 1}).status_code
        == 200
    )
    same = client.get(
        EXPORT, params={"exportacao_id": frozen["exportacao_id"]}, headers=headers
    ).json()
    assert same == frozen
    current = client.get(EXPORT, headers=headers).json()
    assert current["items"][0]["operacao"] == "archive" and current["items"][0]["revisao"] == 2
    assert current["items"][0]["quantidade_acoes"] == 0
    with Session(engine) as session, session.begin():
        session.get(IntegrationExport, frozen["exportacao_id"]).expira_em = datetime.now(
            UTC
        ) - timedelta(seconds=1)
    assert (
        client.get(
            EXPORT, params={"exportacao_id": frozen["exportacao_id"]}, headers=headers
        ).status_code
        == 410
    )


def test_service_limit_and_export_owner_binding(authenticated):
    client, engine, _ = authenticated
    issued = issue(client)
    headers = {"Authorization": "Bearer " + issued["token"]}
    frozen = client.get(EXPORT, headers=headers).json()
    assert frozen["items"] == [] and frozen["total_pages"] == 1 and frozen["quantidade_acoes"] == 0
    other = issue(client)
    assert (
        client.get(
            EXPORT,
            params={"exportacao_id": frozen["exportacao_id"]},
            headers={"Authorization": "Bearer " + other["token"]},
        ).status_code
        == 410
    )
    assert client.get(EXPORT, params={"page": 2}, headers=headers).status_code == 422
    with Session(engine) as session, session.begin():
        row = session.get(IntegrationCredential, issued["credencial"]["id"])
        row.janela_minuto = int(datetime.now(UTC).timestamp() // 60)
        row.chamadas_janela = 60
    limited = client.get("/api/v1/integracoes/health", headers=headers)
    assert limited.status_code == 429 and "retry-after" in limited.headers


@pytest.mark.parametrize(
    "extra", [{"escopo": "acoes.write"}, {"validade_dias": 0}, {"validade_dias": "30"}]
)
def test_no_privilege_escalation_or_invalid_lifetime(authenticated, extra):
    client, _, _ = authenticated
    assert (
        client.post(
            BASE, json={"nome": "Token de teste", "password": PASSWORD, **extra}
        ).status_code
        == 422
    )


def test_step_up_retries_bounded_without_secret_in_error(authenticated):
    client, _, _ = authenticated
    for _ in range(5):
        response = client.post(BASE, json={"nome": "Token de teste", "password": "bad-synthetic"})
        assert response.status_code == 401 and "bad-synthetic" not in response.text
    assert (
        client.post(BASE, json={"nome": "Token de teste", "password": PASSWORD}).status_code == 429
    )


def test_multiple_pages_are_frozen_and_totals_do_not_repeat(authenticated):
    client, engine, repo = authenticated
    with Session(engine) as session, session.begin():
        for index in range(101):
            row = save_action(
                session,
                ActionInput(
                    nome=f"Ação sintética {index}",
                    resumo_publico="Resumo sintético aprovado.",
                    locais=[{"municipio_ibge": "2508901", "nome_local": ""}],
                ),
                repo.professional,
            )
            change_status(session, row["id"], 1, "validada", repo.professional)
            change_status(session, row["id"], 2, "publicada", repo.professional)
    issued = issue(client)
    headers = {"Authorization": "Bearer " + issued["token"]}
    first = client.get(EXPORT, headers=headers).json()
    second = client.get(
        EXPORT, params={"page": 2, "exportacao_id": first["exportacao_id"]}, headers=headers
    ).json()
    assert len(first["items"]) == 100 and len(second["items"]) == 1
    assert first["quantidade_acoes"] == second["quantidade_acoes"] == 101
    assert first["checksum"] == second["checksum"]
    assert len({row["acao_id"] for row in first["items"] + second["items"]}) == 101
    newer = create(client)
    unchanged = client.get(
        EXPORT, params={"page": 2, "exportacao_id": first["exportacao_id"]}, headers=headers
    ).json()
    assert unchanged == second and newer["id"] not in {
        row["acao_id"] for row in first["items"] + second["items"]
    }


def test_never_expiring_token_preserves_finite_tokens_and_supports_rotation(authenticated):
    client, engine, _ = authenticated
    finite = issue(client)
    with Session(engine) as session:
        original_expiry = session.get(IntegrationCredential, finite["credencial"]["id"]).expira_em
    response = client.post(
        BASE, json={"nome": "Agenda permanente", "validade_dias": None, "password": PASSWORD}
    )
    assert response.status_code == 201, response.text
    permanent = response.json()
    assert permanent["credencial"]["expira_em"] is None
    assert permanent["credencial"]["status"] == "ativa"
    headers = {"Authorization": "Bearer " + permanent["token"]}
    assert client.get("/api/v1/integracoes/health", headers=headers).status_code == 200
    listing = client.get(BASE).json()
    assert (
        next(row for row in listing if row["id"] == permanent["credencial"]["id"])["expira_em"]
        is None
    )
    with Session(engine) as session:
        assert (
            session.get(IntegrationCredential, finite["credencial"]["id"]).expira_em
            == original_expiry
        )
    rotated = client.post(
        BASE + f"/{permanent['credencial']['id']}/rotacionar",
        json={
            "nome": "Agenda permanente substituta",
            "validade_dias": None,
            "password": PASSWORD,
        },
    )
    assert rotated.status_code == 201 and rotated.json()["credencial"]["expira_em"] is None
    assert client.get("/api/v1/integracoes/health", headers=headers).status_code == 401
    replacement = rotated.json()
    headers = {"Authorization": "Bearer " + replacement["token"]}
    assert client.get("/api/v1/integracoes/health", headers=headers).status_code == 200
    assert (
        client.post(
            BASE + f"/{replacement['credencial']['id']}/revogar", json={"password": PASSWORD}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/integracoes/health", headers=headers).status_code == 401


def test_never_expiring_tokens_count_toward_active_limit(authenticated):
    client, engine, repo = authenticated
    with Session(engine) as session, session.begin():
        repository = SqlCredentialRepository(session)
        for index in range(20):
            repository.create(
                CredentialInput(nome=f"Permanente {index}", validade_dias=None, password=PASSWORD),
                repo.professional,
            )
    limited = client.post(BASE, json={"nome": "Excede limite", "password": PASSWORD})
    assert limited.status_code == 409


def test_existing_sqlite_migration_preserves_credentials(tmp_path):
    from app.domain.contracts import Professional
    from app.infrastructure.local_migrations import allow_nonexpiring_local_tokens
    from app.infrastructure.models import Base
    from cryptography.fernet import Fernet

    engine = create_engine("sqlite:///" + (tmp_path / "legacy.sqlite3").as_posix())
    legacy = IntegrationCredential.__table__.to_metadata(MetaData())
    legacy.c.expira_em.nullable = False
    legacy.create(engine)
    Base.metadata.create_all(engine)
    professional = Professional(
        profissional_id="test-tech", nome="Teste", tipo_login="administracao", equipe="tecnologia"
    )
    with Session(engine) as session, session.begin():
        finite = SqlCredentialRepository(session).create(
            CredentialInput(nome="Token antigo", password=PASSWORD), professional
        )
    key = Fernet.generate_key().decode()
    assert allow_nonexpiring_local_tokens(engine, key, tmp_path / "backups", apply=True)
    assert next(
        column
        for column in inspect(engine).get_columns(legacy.name)
        if column["name"] == "expira_em"
    )["nullable"]
    assert not allow_nonexpiring_local_tokens(engine, key, tmp_path / "backups", apply=True)
    assert len(list((tmp_path / "backups").glob("*.fernet"))) == 1
    with Session(engine) as session, session.begin():
        assert session.get(IntegrationCredential, finite["credencial"]["id"]).expira_em is not None
        permanent = SqlCredentialRepository(session).create(
            CredentialInput(nome="Token novo", password=PASSWORD, validade_dias=None), professional
        )
        assert permanent["credencial"]["expira_em"] is None
    engine.dispose()
