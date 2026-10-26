"""Migrações aditivas da publicação; preserva identidades e dados operacionais."""

import argparse
import hashlib
import re
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from import_historical_pdf import backup_module
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["agenda", "map"], required=True)
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
    ).execution_options(schema_translate_map={None: "actions_map"})
    with engine.connect() as connection, connection.begin():
        connection.execute(text("SET LOCAL lock_timeout='5s'"))
        connection.execute(text("SET LOCAL statement_timeout='30s'"))
        before = connection.execute(
            text(
                "SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='public.profissionais_cadastrados'::regclass"
            )
        ).one()
        people = connection.scalar(text("SELECT count(*) FROM actions_map.acoes_map_beneficiarios"))
        if not args.apply:
            print("PUBLICATION_PREFLIGHT_OK: nenhuma alteração executada.")
            return
        backup_module(connection, private["BENEFICIARIES_KEY"])
        if args.target == "map":
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtext('actions_map.migration'))")
            )
            current = connection.scalar(text("SELECT version_num FROM actions_map.alembic_version"))
            if current not in {"0003_private_file_import", "0004_remove_drafts"}:
                raise ValueError("Versão de origem inesperada.")
            config = Config(str(ROOT / "backend/alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, "0004_remove_drafts")
        else:
            migration = ROOT.parent / "agenda-digital/src/lib/migrations/actions-map-20261026.ts"
            source = migration.read_text(encoding="utf-8").replace("\r\n", "\n")
            checksum = hashlib.sha256((migration.name + "\n" + source).encode()).hexdigest()
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended('agenda-schema-migration',0))")
            )
            previous = connection.scalar(
                text("SELECT checksum FROM public.agenda_schema_migrations WHERE id='202610260001'")
            )
            if previous and previous != checksum:
                raise ValueError("Checksum da migração divergiu.")
            if not previous:
                if connection.scalar(text("SELECT to_regclass('agenda_actions.inbox')")):
                    raise ValueError("Schema sem recibo; revisão manual necessária.")
                statements = re.findall(r"await sql`(.*?)`", source, re.DOTALL)
                if len(statements) != 4 or any("${" in statement for statement in statements):
                    raise ValueError("Migração com formato não previsto.")
                for statement in statements:
                    connection.execute(text(statement))
                connection.execute(
                    text(
                        "INSERT INTO public.agenda_schema_migrations(id,name,checksum,mode) VALUES('202610260001','Resumos institucionais do AC Actions Map',:checksum,'applied')"
                    ),
                    {"checksum": checksum},
                )
        after = connection.execute(
            text(
                "SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='public.profissionais_cadastrados'::regclass"
            )
        ).one()
        if before != after or people != connection.scalar(
            text("SELECT count(*) FROM actions_map.acoes_map_beneficiarios")
        ):
            raise ValueError("Validação de preservação falhou.")
    print(
        "PUBLICATION_MIGRATION_OK: "
        + args.target
        + "; backup verificado; registros e RLS preservados."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- fronteira administrativa, sem segredos nos erros.
        print("PUBLICATION_MIGRATION_FAILED: " + type(error).__name__)
        raise SystemExit(1) from None
