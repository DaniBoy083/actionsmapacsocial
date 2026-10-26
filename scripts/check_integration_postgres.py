"""Testa migração/grants/cota concorrente em PostgreSQL local descartável, sem .env."""

import argparse
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.domain.contracts import Professional
from app.domain.integrations import CredentialInput
from app.infrastructure.integrations import (
    SqlCredentialRepository,
    consume_service_token,
    export_page,
)
from app.infrastructure.models import Base, IntegrationCredential, IntegrationExport


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin", type=Path, required=True)
    args = parser.parse_args()
    suffix = ".exe" if os.name == "nt" else ""
    root = ROOT / "tmp"
    root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="integration-pg-", dir=root))
    data = directory / "data"
    password_file = directory / "password"
    password = secrets.token_hex(32)
    password_file.write_text(password, encoding="utf-8")
    with socket.socket() as port_lease:
        port_lease.bind(("127.0.0.1", 0))
        port = port_lease.getsockname()[1]

    def postgres(name, *arguments):
        print("POSTGRES_LOCAL: " + name, flush=True)
        result = subprocess.run(
            [str(args.bin / (name + suffix)), *map(str, arguments)],
            stdout=subprocess.DEVNULL if name == "pg_ctl" else subprocess.PIPE,
            stderr=subprocess.DEVNULL if name == "pg_ctl" else subprocess.PIPE,
            timeout=60,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode:
            raise RuntimeError("Falha no executável local " + name)

    started = False
    engine = None
    try:
        postgres(
            "initdb",
            "-D",
            data,
            "-U",
            "acm_test",
            "--pwfile",
            password_file,
            "--auth=scram-sha-256",
            "--encoding=UTF8",
            "--locale=C",
        )
        password_file.unlink()
        started = True
        postgres(
            "pg_ctl",
            "-D",
            data,
            "-l",
            directory / "postgres.log",
            "-o",
            f"-h 127.0.0.1 -p {port}",
            "-w",
            "start",
        )
        engine = create_engine(
            f"postgresql+psycopg://acm_test:{password}@127.0.0.1:{port}/postgres",
            hide_parameters=True,
            pool_size=12,
            max_overflow=0,
        ).execution_options(schema_translate_map={None: "actions_map"})
        with engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA actions_map"))
            connection.execute(text("CREATE ROLE ac_actions_map_runtime"))
            # Baseline próprio equivalente a 0004; nenhuma tabela institucional é necessária.
            Base.metadata.create_all(
                connection,
                tables=[
                    table
                    for table in Base.metadata.sorted_tables
                    if table not in {IntegrationCredential.__table__, IntegrationExport.__table__}
                ],
            )
            connection.execute(
                text(
                    "CREATE TABLE actions_map.alembic_version(version_num varchar(32) PRIMARY KEY)"
                )
            )
            connection.execute(
                text("INSERT INTO actions_map.alembic_version VALUES('0004_remove_drafts')")
            )
            connection.execute(text("GRANT USAGE ON SCHEMA actions_map TO ac_actions_map_runtime"))
            connection.execute(
                text(
                    "GRANT SELECT,INSERT ON actions_map.acoes_map_auditoria TO ac_actions_map_runtime"
                )
            )
            connection.execute(
                text(
                    "GRANT SELECT ON actions_map.acoes_map_acoes,actions_map.acoes_map_integracoes_outbox TO ac_actions_map_runtime"
                )
            )
            config = Config(str(ROOT / "backend/alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, "0005_integration_tokens")
            connection.execute(
                text("""INSERT INTO actions_map.acoes_map_credenciais_integracao
                (id,nome,prefixo,sufixo,token_hash,escopo,criado_por,criado_em,expira_em,chamadas,janela_minuto,chamadas_janela)
                VALUES('00000000-0000-0000-0000-000000000001','Prazo existente','synthetic','only',:hash,'acoes.resumos.read',
                'synthetic-tech',now(),'2030-01-01T00:00:00Z',0,0,0)"""),
                {"hash": "0" * 64},
            )
            before = connection.execute(
                text(
                    "SELECT token_hash,expira_em FROM actions_map.acoes_map_credenciais_integracao WHERE nome='Prazo existente'"
                )
            ).one()
            command.upgrade(config, "0006_nonexpiring_tokens")
            assert (
                before
                == connection.execute(
                    text(
                        "SELECT token_hash,expira_em FROM actions_map.acoes_map_credenciais_integracao WHERE nome='Prazo existente'"
                    )
                ).one()
            )
        with Session(engine) as session, session.begin():
            session.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
            assert not session.scalar(
                text(
                    "SELECT has_table_privilege(current_user,'actions_map.acoes_map_credenciais_integracao','DELETE')"
                )
            )
            issued = SqlCredentialRepository(session).create(
                CredentialInput(
                    nome="Agenda sintética PostgreSQL",
                    password="synthetic-only",
                    validade_dias=None,
                ),
                Professional(
                    profissional_id="synthetic-tech",
                    nome="Teste",
                    tipo_login="administracao",
                    equipe="tecnologia",
                ),
            )
            assert issued["credencial"]["expira_em"] is None
            assert export_page(session, issued["credencial"]["id"], 1, None)["items"] == []
        if datetime.now(UTC).second > 54:
            time.sleep(61 - datetime.now(UTC).second)

        def consume(_):
            with Session(engine) as session, session.begin():
                session.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
                return consume_service_token(session, "Bearer " + issued["token"])[1]

        with ThreadPoolExecutor(max_workers=12) as workers:
            results = list(workers.map(consume, range(70)))
        assert results.count(200) == 60 and results.count(429) == 10
        with Session(engine) as session, session.begin():
            session.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
            SqlCredentialRepository(session).revoke(
                issued["credencial"]["id"],
                Professional(
                    profissional_id="synthetic-tech",
                    nome="Teste",
                    tipo_login="administracao",
                    equipe="tecnologia",
                ),
            )
        assert consume(None) == 401
        print(
            "POSTGRES_INTEGRATION_OK: migrações 0005/0006, prazo existente preservado, token sem expiração, grants, exportação, revogação e cota 60/70 sob 12 trabalhadores."
        )
    finally:
        if engine:
            engine.dispose()
        if started:
            postgres("pg_ctl", "-D", data, "-m", "fast", "-w", "stop")
        if password_file.exists():
            password_file.unlink()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- ambiente sintético; não imprimir credenciais.
        print("POSTGRES_INTEGRATION_FAILED: " + type(error).__name__)
        raise SystemExit(1) from None
