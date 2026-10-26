"""Provisionamento explícito e aditivo do módulo. Nunca exibe DSN, senhas ou chaves."""

import argparse
import json
import secrets
import shutil
import subprocess
from pathlib import Path

from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "artifacts/production-config.env"
ROLE = "ac_actions_map_runtime"
ORIGIN = "https://actionsmapacsocial.vercel.app"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--configure-vercel", action="store_true")
    args = parser.parse_args()
    source = dotenv_values(ROOT / ".env.local")
    admin_url = source.get("DATABASE_URL")
    if not admin_url:
        raise RuntimeError("Configuração institucional ausente.")
    parsed = make_url(admin_url)
    if parsed.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}:
        raise RuntimeError("A conexão administrativa exige TLS.")
    admin_engine = create_engine(
        parsed.set(drivername="postgresql+psycopg"),
        hide_parameters=True,
        connect_args={"connect_timeout": 8},
    )
    with admin_engine.connect() as connection:
        metadata = (
            connection.execute(
                text(
                    "SELECT table_schema,table_name,column_name,data_type FROM information_schema.columns WHERE table_schema IN ('public','portal') ORDER BY 1,2,ordinal_position"
                )
            )
            .mappings()
            .all()
        )
        tables = (
            connection.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='actions_map' ORDER BY 1"
                )
            )
            .scalars()
            .all()
        )
        role_exists = connection.scalar(
            text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=:role)"), {"role": ROLE}
        )
    print(
        json.dumps(
            {
                "preflight": "OK",
                "existing_module_tables": len(tables),
                "runtime_role_exists": role_exists,
            }
        )
    )
    if not args.apply:
        return 0
    if role_exists and not PRIVATE.exists():
        raise RuntimeError(
            "Credencial existente: recupere o segredo antes de continuar; não será rotacionado automaticamente."
        )
    if not PRIVATE.exists():
        password = secrets.token_urlsafe(48)
        runtime_url = parsed.set(username=ROLE, password=password).render_as_string(
            hide_password=False
        )
        values = {
            "APP_ENV": "production",
            "ACTIONS_DATABASE_URL": runtime_url,
            "SESSION_SECRET": secrets.token_urlsafe(48),
            "BENEFICIARIES_KEY": Fernet.generate_key().decode(),
            "FRONTEND_ORIGIN": ORIGIN,
            "AGENDA_WEB_URL": "https://agenda-digital-ac-social.vercel.app",
        }
        PRIVATE.parent.mkdir(parents=True, exist_ok=True)
        PRIVATE.write_text(
            "".join(f"{key}={json.dumps(value)}\n" for key, value in values.items()),
            encoding="utf-8",
        )
        (PRIVATE.parent / "production-before-module-schema.json").write_text(
            json.dumps([dict(row) for row in metadata], indent=2), encoding="utf-8"
        )
    values = dotenv_values(PRIVATE)
    with admin_engine.connect() as connection, connection.begin():
        assert connection.scalar(
            text("SELECT pg_try_advisory_xact_lock(hashtext('actions_map.migration'))")
        ), "Outra migração está em andamento."
        connection.execute(text("SET LOCAL lock_timeout='5s'"))
        connection.execute(text("SET LOCAL statement_timeout='30s'"))
        config = Config(str(ROOT / "backend/alembic.ini"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        raw = connection.connection.driver_connection
        if not role_exists:
            runtime_password = make_url(values["ACTIONS_DATABASE_URL"]).password
            raw.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION"
                ).format(sql.Identifier(ROLE), sql.Literal(runtime_password))
            )
        raw.execute(
            sql.SQL("GRANT USAGE ON SCHEMA public, actions_map TO {}").format(sql.Identifier(ROLE))
        )
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
        raw.execute(sql.SQL("REVOKE ALL ON SCHEMA actions_map FROM PUBLIC"))
        raw.execute(
            sql.SQL(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA actions_map TO {}"
            ).format(sql.Identifier(ROLE))
        )
        raw.execute(
            sql.SQL("REVOKE INSERT,UPDATE,DELETE ON actions_map.alembic_version FROM {}").format(
                sql.Identifier(ROLE)
            )
        )
        raw.execute(
            sql.SQL("REVOKE UPDATE,DELETE ON actions_map.acoes_map_auditoria FROM {}").format(
                sql.Identifier(ROLE)
            )
        )
        updated = (
            connection.execute(
                text(
                    "SELECT table_schema,table_name,column_name,data_type FROM information_schema.columns WHERE table_schema IN ('public','portal') ORDER BY 1,2,ordinal_position"
                )
            )
            .mappings()
            .all()
        )
        assert [dict(row) for row in updated] == [dict(row) for row in metadata], (
            "Estrutura compartilhada divergiu."
        )
        assert not connection.scalar(
            text("SELECT has_table_privilege(:role,'public.profissionais_cadastrados','INSERT')"),
            {"role": ROLE},
        )
    runtime_engine = create_engine(
        make_url(values["ACTIONS_DATABASE_URL"]).set(drivername="postgresql+psycopg"),
        hide_parameters=True,
        connect_args={"connect_timeout": 8},
    )
    with runtime_engine.connect() as connection:
        assert connection.scalar(text("SELECT 1")) == 1
        assert (
            connection.scalar(text("SELECT version_num FROM actions_map.alembic_version"))
            == "0002_authentication_lookup"
        )
        assert connection.scalar(text("SELECT count(*) FROM actions_map.acoes_map_acoes")) == 0
    print(
        "MIGRATION_OK: schema isolado; identidade preservada; credencial sem escrita nos profissionais."
    )
    if args.configure_vercel:
        cli = shutil.which("vercel.cmd") or shutil.which("vercel")
        if not cli:
            raise RuntimeError("CLI Vercel indisponível.")
        for key, value in values.items():
            arguments = [cli, "env", "add", key, "production", "--non-interactive"]
            if key in {"ACTIONS_DATABASE_URL", "SESSION_SECRET", "BENEFICIARIES_KEY"}:
                arguments.append("--sensitive")
            response = subprocess.run(
                arguments,
                check=False,
                input=value.encode(),
                capture_output=True,
                cwd=ROOT,
                timeout=45,
            )
            if response.returncode:
                raise RuntimeError(
                    f"Não foi possível provisionar {key}; consulte a configuração sem exibir valores."
                )
            print(f"VERCEL_CONFIG_OK: {key}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # noqa: BLE001 -- fronteira operacional: nunca imprimir DSN/credenciais.
        print(
            "PROVISION_ERRO: operação interrompida; consulte o estado do schema/variáveis antes de repetir."
        )
        raise SystemExit(1) from None
