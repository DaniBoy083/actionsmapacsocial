"""Prévia por padrão; aplica somente 0005 após backup cifrado consistente e verificado."""

import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from import_historical_pdf import backup_module
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    private = dotenv_values(ROOT / "artifacts/production-config.env")
    url = make_url(dotenv_values(ROOT / ".env.local")["DATABASE_URL"])
    if url.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}:
        raise ValueError("TLS obrigatório.")
    engine = create_engine(
        url.set(drivername="postgresql+psycopg"),
        hide_parameters=True,
        connect_args={"connect_timeout": 8},
        isolation_level="REPEATABLE READ",
    ).execution_options(schema_translate_map={None: "actions_map"})
    with engine.connect() as connection, connection.begin():
        connection.execute(text("SET LOCAL lock_timeout='5s'"))
        connection.execute(text("SET LOCAL statement_timeout='30s'"))
        if not connection.scalar(
            text("SELECT pg_try_advisory_xact_lock(hashtext('actions_map.migration'))")
        ):
            raise RuntimeError("Outra migração está em execução.")
        revision = connection.scalar(text("SELECT version_num FROM actions_map.alembic_version"))
        if revision not in {"0004_remove_drafts", "0005_integration_tokens"}:
            raise ValueError("Versão de origem inesperada.")
        before = connection.execute(
            text(
                "SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='public.profissionais_cadastrados'::regclass"
            )
        ).one()
        counts = connection.execute(
            text(
                "SELECT (SELECT count(*) FROM actions_map.acoes_map_acoes),(SELECT count(*) FROM actions_map.acoes_map_beneficiarios)"
            )
        ).one()
        if not args.apply:
            print("INTEGRATION_PREFLIGHT_OK: duas tabelas novas; nenhuma migração aplicada.")
            return
        backup_module(connection, private["BENEFICIARIES_KEY"])
        config = Config(str(ROOT / "backend/alembic.ini"))
        config.attributes["connection"] = connection
        command.upgrade(config, "0005_integration_tokens")
        after = connection.execute(
            text(
                "SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='public.profissionais_cadastrados'::regclass"
            )
        ).one()
        if (
            before != after
            or counts
            != connection.execute(
                text(
                    "SELECT (SELECT count(*) FROM actions_map.acoes_map_acoes),(SELECT count(*) FROM actions_map.acoes_map_beneficiarios)"
                )
            ).one()
        ):
            raise RuntimeError("Validação de preservação falhou.")
    print("INTEGRATION_MIGRATION_OK: backup verificado; ações, beneficiários e RLS preservados.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- fronteira administrativa sem segredos no erro.
        print("INTEGRATION_MIGRATION_FAILED: " + type(error).__name__)
        raise SystemExit(1) from None
