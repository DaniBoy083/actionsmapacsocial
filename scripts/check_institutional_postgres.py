"""Testa revisão 0007 em PostgreSQL descartável local; não usa .env ou bancos existentes."""

import argparse
import base64
import io
import os
import secrets
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.api.action_filters import filter_institutional
from app.domain.contracts import ActionInput, Professional
from app.infrastructure.actions import save_action
from app.infrastructure.institutional_grants import IMMUTABLE_INSTITUTIONAL_GRANTS
from app.infrastructure.models import Action, ActionLogo, Base, InstitutionalRevision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin", type=Path, required=True)
    args = parser.parse_args()
    directory = Path(tempfile.mkdtemp(prefix="institutional-pg-", dir=ROOT / "tmp"))
    data = directory / "data"
    password_file = directory / "password"
    password = secrets.token_hex(32)
    password_file.write_text(password, encoding="utf-8")
    with socket.socket() as lease:
        lease.bind(("127.0.0.1", 0))
        port = lease.getsockname()[1]

    def postgres(name, *arguments):
        result = subprocess.run(
            [
                str(args.bin / (name + (".exe" if os.name == "nt" else ""))),
                *map(str, arguments),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode:
            raise RuntimeError("Falha no executável local " + name)

    engine = None
    started = False
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
        ).execution_options(schema_translate_map={None: "actions_map"})
        with engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA actions_map"))
            connection.execute(text("CREATE ROLE ac_actions_map_runtime"))
            Base.metadata.create_all(
                connection,
                tables=[
                    table
                    for table in Base.metadata.sorted_tables
                    if table
                    not in {ActionLogo.__table__, InstitutionalRevision.__table__}
                ],
            )
            connection.execute(
                text(
                    "ALTER TABLE actions_map.acoes_map_acoes DROP COLUMN institucional"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE actions_map.acoes_map_participacoes DROP COLUMN documento_institucional"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE actions_map.alembic_version(version_num varchar(32) PRIMARY KEY)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO actions_map.alembic_version VALUES ('0006_nonexpiring_tokens')"
                )
            )
            connection.execute(
                text("GRANT USAGE ON SCHEMA actions_map TO ac_actions_map_runtime")
            )
            connection.execute(
                text(
                    "GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA actions_map TO ac_actions_map_runtime"
                )
            )
            connection.execute(
                text(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA actions_map GRANT ALL ON TABLES TO ac_actions_map_runtime"
                )
            )
            config = Config(str(ROOT / "backend/alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, "0007_institutional_metadata")
            command.upgrade(config, "0007_institutional_metadata")
            # Simula a concessão geral do provisionamento e aplica sua regra de restrição.
            connection.execute(
                text(
                    "GRANT ALL ON ALL TABLES IN SCHEMA actions_map TO ac_actions_map_runtime"
                )
            )
            connection.execute(text(IMMUTABLE_INSTITUTIONAL_GRANTS))
            assert (
                connection.scalar(
                    text("SELECT version_num FROM actions_map.alembic_version")
                )
                == "0007_institutional_metadata"
            )
        image = io.BytesIO()
        Image.new("RGB", (96, 96), "red").save(image, "PNG")
        data = ActionInput(
            nome="Ação sintética",
            locais=[{"municipio_ibge": "2507507"}],
            institucional={
                "instrumento": {"tipo": "EMENDA", "numero": "0007", "nome": "Teste"},
                "governo": {
                    "nome": "Órgão teste",
                    "uso_autorizado": True,
                    "conteudo_base64": base64.b64encode(image.getvalue()).decode(),
                },
            },
        )
        professional = Professional(
            profissional_id="synthetic",
            nome="Teste",
            tipo_login="administracao",
            equipe="administracao",
        )
        with Session(engine) as session, session.begin():
            session.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
            created = save_action(session, data, professional)
            assert created["institucional"]["instrumento"]["numero"] == "0007"
            changed = data.model_copy(update={"versao": 1, "nome": "Editada"})
            save_action(session, changed, professional, created["id"])
            assert session.get(InstitutionalRevision, (created["id"], 1)) is not None
            from sqlalchemy import select

            filters = {
                "instrumento": "Teste",
                "numero_instrumento": "0007",
                "autor": "",
                "orgao": "",
                "clinica": "",
                "apoio": "",
            }
            assert (
                session.scalar(filter_institutional(select(Action.id), filters))
                == created["id"]
            )
        for table in ("acoes_map_marcas", "acoes_map_revisoes_institucionais"):
            for operation in ("DELETE", "UPDATE"):
                with engine.begin() as connection:
                    connection.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
                    try:
                        statement = (
                            f"DELETE FROM actions_map.{table}"
                            if operation == "DELETE"
                            else f"UPDATE actions_map.{table} SET criado_em=criado_em"
                        )
                        connection.execute(text(statement))
                    except DBAPIError as error:
                        assert getattr(error.orig, "sqlstate", None) == "42501"
                    else:
                        raise AssertionError(
                            "Runtime não deve alterar histórico/marcas."
                        )
                    connection.rollback()
        print(
            "POSTGRES_INSTITUTIONAL_OK: revisão 0007 idempotente, CRUD/CAS, filtros JSON, histórico e grants imutáveis."
        )
    finally:
        if engine:
            engine.dispose()
        if started:
            postgres("pg_ctl", "-D", directory / "data", "-m", "fast", "-w", "stop")
        if password_file.exists():
            password_file.unlink()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- ambiente sintético; não imprimir credenciais.
        print("POSTGRES_INSTITUTIONAL_FAILED: " + type(error).__name__)
        raise SystemExit(1) from None
