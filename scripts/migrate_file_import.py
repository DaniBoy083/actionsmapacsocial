"""Migração aditiva para arquivos privados; backup cifrado antes da aplicação."""

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
    admin = dotenv_values(ROOT / ".env.local")["DATABASE_URL"]
    parsed = make_url(admin)
    if parsed.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}:
        raise ValueError("TLS obrigatório.")
    engine = create_engine(parsed.set(drivername="postgresql+psycopg"),
                           hide_parameters=True, connect_args={"connect_timeout": 8}).execution_options(
                               schema_translate_map={None: "actions_map"})
    with engine.connect() as connection, connection.begin():
        connection.execute(text("SET LOCAL lock_timeout='5s'"))
        connection.execute(text("SET LOCAL statement_timeout='30s'"))
        if not connection.scalar(text("SELECT pg_try_advisory_xact_lock(hashtext('actions_map.migration'))")):
            raise RuntimeError("Migração já em execução.")
        before = connection.execute(text("SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='public.profissionais_cadastrados'::regclass")).one()
        count_before = connection.scalar(text("SELECT count(*) FROM actions_map.acoes_map_acoes"))
        if not args.apply:
            print("PREFLIGHT_OK: migração aditiva em duas tabelas privadas; nenhuma gravação executada.")
            return
        backup_module(connection, private["BENEFICIARIES_KEY"])
        config = Config(str(ROOT / "backend/alembic.ini"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        # Apenas as duas tabelas novas. Auditoria permanece sem UPDATE/DELETE.
        connection.execute(text("GRANT SELECT,INSERT,UPDATE,DELETE ON actions_map.acoes_map_documentos_importacao, actions_map.acoes_map_partes_importacao TO ac_actions_map_runtime"))
        after = connection.execute(text("SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='public.profissionais_cadastrados'::regclass")).one()
        if before != after or count_before != connection.scalar(text("SELECT count(*) FROM actions_map.acoes_map_acoes")):
            raise RuntimeError("Validação da migração falhou.")
    print("FILE_MIGRATION_OK: backup cifrado verificado; ações e autenticação preservadas.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- não exibir DSN ou dados privados.
        print("FILE_MIGRATION_INTERROMPIDA: " + type(error).__name__)
        raise SystemExit(1) from None
