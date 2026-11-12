"""Prévia por padrão; prepara tabelas clínicas no SQLite local, sem ativar a funcionalidade."""

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.infrastructure.local_migrations import add_local_clinical


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    url = make_url(settings.actions_storage_url)
    if settings.production or url.drivername != "sqlite" or not url.database:
        raise ValueError("Procedimento exclusivo do SQLite de desenvolvimento.")
    database = Path(url.database).resolve()
    if not database.is_relative_to(ROOT):
        raise ValueError("O banco local deve estar neste workspace.")
    if not database.is_file():
        print("Banco novo receberá o modelo atual. Nenhuma alteração aplicada.")
        return
    engine = create_engine(url, hide_parameters=True)
    try:
        changed = add_local_clinical(
            engine,
            settings.beneficiaries_key.get_secret_value(),
            ROOT / "artifacts/private-import/backups",
            apply=args.apply,
        )
        print(
            "Migração e backup verificados; clínica não ativada."
            if changed
            else "Prévia ou tabelas presentes; nenhuma alteração aplicada."
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
