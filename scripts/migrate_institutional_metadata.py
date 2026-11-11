"""Prévia por padrão. Atualiza somente SQLite local, após backup cifrado verificado."""

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.infrastructure.local_migrations import add_local_institutional_metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    parsed = make_url(settings.actions_storage_url)
    if settings.production or parsed.drivername != "sqlite" or not parsed.database:
        raise ValueError("Procedimento exclusivo do SQLite de desenvolvimento.")
    database = Path(parsed.database).resolve()
    if not database.is_relative_to(ROOT):
        raise ValueError("O banco local deve estar neste workspace.")
    if not database.exists():
        print("Banco local ainda não existe; um banco novo recebe o modelo atual.")
        return
    engine = create_engine(parsed, hide_parameters=True)
    try:
        columns = {
            item["name"] for item in inspect(engine).get_columns("acoes_map_acoes")
        }
        pending = "institucional" not in columns
        print(
            "Metadados institucionais: "
            + ("migração pendente." if pending else "coluna presente.")
        )
        changed = add_local_institutional_metadata(
            engine,
            settings.beneficiaries_key.get_secret_value(),
            ROOT / "artifacts/private-import/backups",
            apply=args.apply,
        )
        print(
            "Migração e backup verificados."
            if changed
            else "Nenhuma alteração aplicada."
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
