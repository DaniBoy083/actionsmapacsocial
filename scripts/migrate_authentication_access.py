"""Aplica a consulta de autenticação delegada, sem alterar dados ou desativar RLS."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
ROLE = "ac_actions_map_runtime"


def main():
    configured = dotenv_values(ROOT / "artifacts/production-config.env")
    assert make_url(configured["ACTIONS_DATABASE_URL"]).username == ROLE
    admin = dotenv_values(ROOT / ".env.local")["DATABASE_URL"]
    engine = create_engine(
        make_url(admin).set(drivername="postgresql+psycopg"),
        hide_parameters=True,
        connect_args={"connect_timeout": 8},
    )
    with engine.connect() as connection, connection.begin():
        connection.execute(text("SET LOCAL lock_timeout='5s'"))
        connection.execute(text("SET LOCAL statement_timeout='30s'"))
        assert connection.scalar(
            text("SELECT pg_try_advisory_xact_lock(hashtext('actions_map.migration'))")
        )
        before = connection.execute(
            text(
                "SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='public.profissionais_cadastrados'::regclass"
            )
        ).one()
        config = Config(str(ROOT / "backend/alembic.ini"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        raw = connection.connection.driver_connection
        raw.execute(
            sql.SQL(
                "GRANT EXECUTE ON FUNCTION actions_map.authentication_identity(text,boolean) TO {}"
            ).format(sql.Identifier(ROLE))
        )
        raw.execute(
            sql.SQL(
                "REVOKE SELECT (id,email,password,display_name,user_type) ON public.profissionais_cadastrados FROM {}"
            ).format(sql.Identifier(ROLE))
        )
        raw.execute(
            sql.SQL(
                "REVOKE SELECT (name,professional_ids_json) ON public.equipes_profissionais FROM {}"
            ).format(sql.Identifier(ROLE))
        )
        after = connection.execute(
            text(
                "SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='public.profissionais_cadastrados'::regclass"
            )
        ).one()
        assert before == after
        assert not connection.scalar(
            text("SELECT has_table_privilege(:role,'public.profissionais_cadastrados','INSERT')"),
            {"role": ROLE},
        )
    print(
        "AUTH_MIGRATION_OK: RLS preservado; execução delegada concedida; nenhum registro alterado."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 -- fronteira administrativa, sem mensagens com segredos.
        print("AUTH_MIGRATION_ERRO: operação interrompida sem exibir credenciais.")
        raise SystemExit(1) from None
