"""Provisiona somente segredos locais; nunca exibe valores nem altera o banco."""

import secrets
from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
path = root / ".env.local"
existing = dotenv_values(path)
entries = {
    "SESSION_SECRET": secrets.token_urlsafe(48),
    "BENEFICIARIES_KEY": Fernet.generate_key().decode(),
    "ACTIONS_API_URL": "http://127.0.0.1:8000",
}
with path.open("a", encoding="utf-8") as output:
    for name, value in entries.items():
        if not existing.get(name):
            output.write(f"\n{name}={value}\n")
print("CONFIG_OK: configuração local preservada; segredos ausentes provisionados.")
