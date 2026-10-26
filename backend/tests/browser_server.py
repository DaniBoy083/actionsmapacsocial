"""Servidor exclusivo de E2E. Identidades sintéticas não são carregadas pela aplicação."""

import os
import secrets
import sys
import tempfile
from pathlib import Path

import pymupdf
import uvicorn
from cryptography.fernet import Fernet

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

temporary = tempfile.TemporaryDirectory(prefix="actions-map-e2e-")
directory = Path(temporary.name)
os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": "",
        "ACTIONS_STORAGE_URL": "sqlite:///" + (directory / "test.sqlite3").as_posix(),
        "SESSION_SECRET": secrets.token_urlsafe(48),
        "BENEFICIARIES_KEY": Fernet.generate_key().decode(),
        "FRONTEND_ORIGIN": "http://localhost:3100",
        "AGENDA_WEB_URL": "https://agenda.example.invalid",
    }
)
from app.domain.contracts import Professional
from app.infrastructure import imports
from app.main import app
from app.security.session import identities
from conftest import HASH


class BrowserIdentities:
    def find(self, value, by_id=False):
        team = "administracao" if value in {"admin@example.invalid", "test-admin"} else "tecnologia"
        identifier = "test-admin" if team == "administracao" else "test-tech"
        if value not in {
            "admin@example.invalid",
            "test@example.invalid",
            "test-admin",
            "test-tech",
        }:
            return None
        return Professional(
            profissional_id=identifier,
            nome="Profissional de Teste",
            tipo_login="administracao",
            equipe=team,
        ), HASH


pdf = directory / "synthetic.pdf"
with pymupdf.open() as document:
    for index in range(2):
        page = document.new_page()
        page.insert_text((60, 80), "FICHA SINTETICA - TESTE SEM DADOS REAIS")
        page.insert_text((60, 110), f"Nome: Pessoa de teste {index + 1}")
    document.save(pdf)
imports.SOURCE = pdf
app.dependency_overrides[identities] = BrowserIdentities

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8100, access_log=False)
