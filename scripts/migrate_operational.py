"""Prévia por padrão; não executa em PostgreSQL nem habilita clínica ou login."""

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import get_settings
from app.infrastructure.operational_migration import migrate_local


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    url = make_url(settings.actions_storage_url)
    if settings.production or url.drivername != "sqlite" or not url.database:
        raise ValueError("Procedimento exclusivo do SQLite de desenvolvimento.")
    path = Path(url.database).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Banco deve estar no workspace.")
    if not path.is_file():
        print("Banco ainda não criado; nenhuma alteração aplicada.")
        return
    engine = create_engine(url, hide_parameters=True)
    try:
        print(
            json.dumps(
                migrate_local(
                    engine,
                    settings.beneficiaries_key.get_secret_value(),
                    ROOT / "artifacts/private-import/backups",
                    apply=args.apply,
                )
            )
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
