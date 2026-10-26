"""Build gate: valida configurações sem consultar registros ou exibir valores."""

import json

from cryptography.fernet import Fernet
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from app.config import Settings


def check(settings: Settings) -> dict[str, bool]:
    result = {
        "production": settings.production,
        "session_secret": len(settings.session_secret.get_secret_value()) >= 32,
        "origin_https": settings.frontend_origin.startswith("https://"),
        "database_tls": False,
        "encryption": False,
    }
    try:
        url = make_url(settings.database_url.get_secret_value())
        result["database_tls"] = url.drivername in {
            "postgres",
            "postgresql",
            "postgresql+psycopg",
        } and url.query.get("sslmode") in {"require", "verify-ca", "verify-full"}
        Fernet(settings.beneficiaries_key.get_secret_value().encode())
        result["encryption"] = True
    except (ValueError, TypeError, ArgumentError):
        pass
    return result


if __name__ == "__main__":
    checks = check(Settings(_env_file=None))
    print(json.dumps(checks))
    raise SystemExit(0 if all(checks.values()) else 1)
