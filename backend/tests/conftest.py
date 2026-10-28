import hashlib
import os
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.domain.contracts import Professional
from app.infrastructure.models import Base
from app.main import app
from app.security.session import identities

PASSWORD = "Somente-teste-2026"
SALT = "ab" * 16
HASH = (
    SALT
    + ":"
    + hashlib.scrypt(PASSWORD.encode(), salt=SALT.encode(), n=16384, r=8, p=1, dklen=64).hex()
)


class FakeIdentities:
    def __init__(self):
        self.professional = Professional(
            profissional_id="prof-test",
            nome="Profissional de teste",
            tipo_login="administracao",
            equipe="tecnologia",
        )

    def find(self, value, by_id=False):
        if value in {"test@example.invalid", self.professional.profissional_id}:
            return self.professional, HASH
        return None


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-only-" + os.urandom(32).hex())
    monkeypatch.setenv("BENEFICIARIES_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://localhost:3000")
    monkeypatch.setenv("AGENDA_SUMMARIES_URL", "")
    monkeypatch.setenv("AGENDA_SERVICE_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    repo = FakeIdentities()
    app.dependency_overrides[identities] = lambda: repo
    monkeypatch.setattr("app.security.session.get_engine", lambda: engine)
    monkeypatch.setattr("app.api.routes.get_engine", lambda: engine)
    monkeypatch.setattr("app.api.import_files.get_engine", lambda: engine)
    monkeypatch.setattr("app.api.integrations.get_engine", lambda: engine)
    monkeypatch.setattr("app.api.beneficiaries.get_engine", lambda: engine)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, engine, repo
    app.dependency_overrides.clear()
    get_settings.cache_clear()
    engine.dispose()


@pytest.fixture
def authenticated(api_client):
    client, engine, repo = api_client
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "test@example.invalid", "password": PASSWORD},
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 204, response.text
    token = client.get("/api/v1/auth/me").json()["csrf_token"]
    client.headers.update({"Origin": "http://localhost:3000", "X-CSRF-Token": token})
    return client, engine, repo
