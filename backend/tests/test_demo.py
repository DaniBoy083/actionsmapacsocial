"""Demonstração em processo real separado, sem substituir a autenticação dos testes."""

import hashlib
import os
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
from app.config import Settings
from demo import DEMO_PASSWORD, isolated_environment

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "http://localhost:3300"


def environment_fingerprints():
    return {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [ROOT / ".env", ROOT / ".env.local", ROOT / "backend/private/actions.sqlite3"]
        if path.is_file()
    }


@contextmanager
def running_demo(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    before = environment_fingerprints()
    environment = {
        **os.environ,
        "APP_ENV": "development",
        "VERCEL": "",
        "ACTIONS_DATABASE_URL": "postgresql://DO_NOT_CONNECT.invalid/database",
        "AGENDA_SUMMARIES_URL": "https://DO_NOT_SEND.invalid/events",
        "AGENDA_SERVICE_TOKEN": "SYNTHETIC_HOSTILE_INHERITED_TOKEN",
    }
    with (
        tempfile.TemporaryDirectory(prefix="actionsmap-demo-") as runtime,
        (tmp_path / "demo-output.txt").open("w", encoding="utf-8") as output,
    ):
        child = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "backend/demo.py"),
                "--port",
                str(port),
                "--runtime-dir",
                runtime,
            ],
            cwd=ROOT,
            env=environment,
            stdout=output,
            stderr=output,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}/api/v1", timeout=3) as client:
                deadline = time.monotonic() + 30
                while True:
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    if child.poll() is not None or time.monotonic() > deadline:
                        pytest.fail(
                            "Servidor demo não iniciou; confira o log sintético temporário."
                        )
                    time.sleep(0.2)
                yield client
        finally:
            if child.poll() is None:
                if os.name == "nt":
                    # O executável do venv no Windows pode criar outro python.exe.
                    subprocess.run(
                        ["taskkill", "/PID", str(child.pid), "/T", "/F"],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        check=False,
                    )
                else:
                    child.terminate()
            child.wait(timeout=10)
    assert environment_fingerprints() == before


def sign_in(client, email="admin@demo.invalid"):
    client.headers["Origin"] = ORIGIN
    response = client.post("/auth/login", json={"identifier": email, "password": DEMO_PASSWORD})
    assert response.status_code == 204
    me = client.get("/auth/me").json()
    client.headers["X-CSRF-Token"] = me["csrf_token"]
    assert me["demonstracao"] is True and me["agenda_url"] == ""
    return me


def test_demo_cannot_inherit_institutional_settings(tmp_path, monkeypatch):
    for key, value in isolated_environment(tmp_path, 3300).items():
        monkeypatch.setenv(key, value)
    settings = Settings(_env_file=None)
    assert settings.app_env == "demo" and not settings.production
    assert settings.database_url.get_secret_value() == ""
    assert settings.agenda_service_token.get_secret_value() == ""
    assert settings.agenda_summaries_url == settings.agenda_web_url == ""
    assert settings.actions_storage_url.endswith("/demo.sqlite3")
    assert len(settings.session_secret.get_secret_value()) >= 32
    assert settings.beneficiaries_key != settings.clinical_key
    # Nova configuração futura deve ser explicitamente isolada antes de habilitar demo.
    covered = {key.lower() for key in isolated_environment(tmp_path, 3300)}
    assert set(Settings.model_fields) <= covered


def test_demo_auth_rbac_csrf_clinical_and_synthetic_source(tmp_path):
    with running_demo(tmp_path) as client:
        assert client.get("/auth/context").json() == {"demonstracao": True}
        assert client.get("/acoes").status_code == 401
        assert client.get("/indicadores").status_code == 401
        client.headers["Origin"] = ORIGIN
        assert (
            client.post(
                "/auth/login",
                json={
                    "identifier": "admin@demo.invalid",
                    "password": "wrong",
                },
            ).status_code
            == 401
        )
        sign_in(client)
        assert client.get("/tecnologia/saude").status_code == 403
        assert client.get("/tecnologia/tokens").status_code == 403
        actions = client.get("/acoes").json()
        assert actions["total"] == 3
        assert sum(item["beneficiarios"] for item in actions["items"]) == 12
        assert {item["status"] for item in actions["items"]} == {"em_revisao", "validada"}
        action = actions["items"][0]
        client.headers.pop("X-CSRF-Token")
        assert client.post("/acoes", json={}).status_code == 403
        sign_in(client, "tecnologia@demo.invalid")
        assert client.get("/tecnologia/saude").json()["banco"] == "DB_ERRO"
        assert client.post("/tecnologia/sincronizar-agenda", json={}).status_code == 403
        assert client.post("/importacoes/arquivos", json={}).status_code == 403
        assert client.get("/integracoes/v1/acoes/resumos").status_code == 403
        source = client.post("/importacoes/preview", json={})
        assert source.status_code == 200 and source.json()["paginas"] == 2
        image = client.get(f"/importacoes/{source.json()['id']}/paginas/1")
        assert image.status_code == 200 and image.headers["content-type"] == "image/png"
        published = next(item for item in actions["items"] if "João Pessoa" in item["nome"])
        url = f"/acoes/{published['id']}/beneficiarios"
        people = client.get(url).json()["items"]
        assert all(person["nome"].startswith("Pessoa fictícia DEMO") for person in people)
        records = [client.get(f"{url}/{person['id']}/clinica") for person in people]
        assert sum(record.status_code == 200 for record in records) == 1
        assert all(record.status_code in {200, 403} for record in records)
        assert client.post("/auth/logout", json={}).status_code == 204
        assert client.get("/acoes/" + action["id"]).status_code == 401


def test_demo_restart_gets_new_dataset_and_session(tmp_path):
    with running_demo(tmp_path) as client:
        sign_in(client)
        first = client.get("/acoes").json()["items"][0]
        cookie = client.cookies.get("ac_actions_demo_session")
        assert client.cookies.get("ac_actions_session") is None
        assert (
            client.request(
                "DELETE", "/acoes/" + first["id"], json={"versao": first["versao"]}
            ).status_code
            == 200
        )
    with running_demo(tmp_path) as client:
        client.cookies.set("ac_actions_demo_session", cookie)
        assert client.get("/acoes").status_code == 401
        client.cookies.clear()
        sign_in(client)
        actions = client.get("/acoes").json()
        assert actions["total"] == 3
        assert first["id"] not in {item["id"] for item in actions["items"]}


@pytest.mark.parametrize("flag", [{"APP_ENV": "production"}, {"VERCEL": "1"}])
def test_demo_refuses_production(flag):
    child = subprocess.run(
        [sys.executable, str(ROOT / "backend/demo.py")],
        cwd=ROOT,
        env={**os.environ, "APP_ENV": "development", "VERCEL": "", **flag},
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert child.returncode != 0
    assert b"uvicorn.run" not in child.stdout


def test_normal_runtime_has_no_demo_credentials(api_client):
    client, _, _ = api_client
    assert client.get("/api/v1/auth/context").json() == {"demonstracao": False}
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "admin@demo.invalid",
            "password": DEMO_PASSWORD,
        },
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 401


def test_demo_launcher_refuses_occupied_port():
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        port = occupied.getsockname()[1]
        other = 3300 if port != 3300 else 3301
        child = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/demo.py"),
                "--frontend-port",
                str(port),
                "--backend-port",
                str(other),
            ],
            cwd=ROOT,
            env={**os.environ, "APP_ENV": "development", "VERCEL": ""},
            capture_output=True,
            timeout=10,
            check=False,
        )
    assert child.returncode == 2
    assert b"ocupada" in child.stderr
