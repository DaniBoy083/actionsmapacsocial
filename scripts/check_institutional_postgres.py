"""Testa revisões 0007–0010 em PostgreSQL descartável local; não usa bancos existentes."""

import argparse
import base64
import io
import os
import secrets
import socket
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi import HTTPException
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.api.action_filters import filter_institutional
from app.config import get_settings
from app.domain.clinical import ClinicalDesignationInput, ClinicalInput
from app.domain.contracts import ActionInput, Professional
from app.domain.operational import OperationalAccountInput
from app.domain.staff import AssignmentInput, AssignmentUpdate, StaffInput
from app.infrastructure.account_grants import ACCOUNT_GRANTS
from app.infrastructure.actions import save_action
from app.infrastructure.clinical import SqlClinicalRepository
from app.infrastructure.clinical_grants import CLINICAL_GRANTS
from app.infrastructure.institutional_grants import IMMUTABLE_INSTITUTIONAL_GRANTS
from app.infrastructure.models import (
    Action,
    ActionLogo,
    Base,
    Beneficiary,
    ClinicalRecord,
    ClinicalRevision,
    InstitutionalRevision,
    OperationalAccount,
    OperationalSession,
    Participation,
    StaffAssignment,
    StaffRecord,
    StaffRevision,
)
from app.infrastructure.operational_access import save_account
from app.infrastructure.operational_grants import OPERATIONAL_GRANTS
from app.infrastructure.operational_migration import TABLES
from app.infrastructure.staff import SqlStaffRepository
from app.infrastructure.staff_grants import STAFF_GRANTS


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
                    not in {
                        *TABLES,
                        ActionLogo.__table__,
                        InstitutionalRevision.__table__,
                        StaffRecord.__table__,
                        StaffAssignment.__table__,
                        StaffRevision.__table__,
                        ClinicalRecord.__table__,
                        ClinicalRevision.__table__,
                        OperationalAccount.__table__,
                        OperationalSession.__table__,
                    }
                ],
            )
            connection.execute(
                text("ALTER TABLE actions_map.acoes_map_acoes DROP COLUMN institucional")
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
                text("INSERT INTO actions_map.alembic_version VALUES ('0006_nonexpiring_tokens')")
            )
            connection.execute(text("GRANT USAGE ON SCHEMA actions_map TO ac_actions_map_runtime"))
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
            command.upgrade(config, "0008_staff_assignments")
            command.upgrade(config, "0008_staff_assignments")
            command.upgrade(config, "0009_clinical_fields")
            command.upgrade(config, "0009_clinical_fields")
            command.upgrade(config, "0010_institutions_and_cases")
            command.upgrade(config, "0010_institutions_and_cases")
            command.upgrade(config, "0011_operational_accounts")
            command.upgrade(config, "0011_operational_accounts")
            # Simula a concessão geral do provisionamento e aplica sua regra de restrição.
            connection.execute(
                text("GRANT ALL ON ALL TABLES IN SCHEMA actions_map TO ac_actions_map_runtime")
            )
            connection.execute(text(IMMUTABLE_INSTITUTIONAL_GRANTS))
            connection.execute(text(STAFF_GRANTS))
            connection.execute(text(CLINICAL_GRANTS))
            connection.execute(text(OPERATIONAL_GRANTS))
            connection.execute(text(ACCOUNT_GRANTS))
            assert (
                connection.scalar(text("SELECT version_num FROM actions_map.alembic_version"))
                == "0011_operational_accounts"
            )
        image = io.BytesIO()
        Image.new("RGB", (96, 96), "red").save(image, "PNG")
        data = ActionInput(
            nome="Ação sintética",
            locais=[{"municipio_ibge": "2507507"}],
            institucional={
                "contratantes": [{"nome": "Contratante sintético", "tipo": "OUTRO"}],
                "apoiadores": [
                    {
                        "nome": "Apoiador sintético",
                        "tipo": "CLINICA",
                        "modalidade": "PARCIAL",
                    }
                ],
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
            assert session.scalar(filter_institutional(select(Action.id), filters)) == created["id"]
        from app.api import routes

        routes.get_engine = lambda: engine
        page = routes.list_actions(
            busca="",
            municipio="2507507",
            status="",
            categoria="",
            inicio="",
            fim="",
            pagina=1,
            tamanho=10,
            filtros=filters,
            _professional=professional,
        )
        assert page["total"] == 1 and page["items"][0]["id"] == created["id"]
        os.environ.update(
            {
                "CLINICAL_FIELDS_ENABLED": "true",
                "CLINICAL_KEY": Fernet.generate_key().decode(),
                "BENEFICIARIES_KEY": Fernet.generate_key().decode(),
                "APP_ENV": "test",
            }
        )
        get_settings.cache_clear()
        with Session(engine) as session, session.begin():
            session.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
            repository = SqlStaffRepository(session)
            staff = repository.save(
                StaffInput(
                    nome="Profissional sintético",
                    categoria="MEDICO",
                    registro_conselho="CRM",
                    registro_numero="000123",
                    registro_uf="PB",
                    habilitacao_validada=True,
                    habilitacao_referencia="Teste",
                    registro_clinico_autorizado=True,
                    autorizacao_clinica_referencia="Teste",
                    identidade_institucional_id=professional.profissional_id,
                ),
                professional,
            )
            assignment = repository.assign(
                created["id"],
                AssignmentInput(
                    profissional_id=staff["id"],
                    acao_versao=2,
                    profissional_versao=1,
                    locais_indices=[0],
                ),
                professional,
            )
            person_id = str(uuid4())
            session.add(Beneficiary(id=person_id, dados_cifrados="synthetic-unused-registration"))
            session.flush()
            session.add(
                Participation(acao_id=created["id"], beneficiario_id=person_id, local_indice=0)
            )
            session.flush()
            clinical = SqlClinicalRepository(session, professional)
            clinical.designation(
                created["id"],
                person_id,
                ClinicalDesignationInput(profissional_id=staff["id"]),
            )
            result = clinical.save(
                created["id"],
                person_id,
                ClinicalInput(campos={"lentes": "SYNTHETIC_CLINICAL_VALUE"}),
            )
            assert result["versao"] == 1
            assert (
                clinical.read(created["id"], person_id)["campos"]["lentes"]
                == "SYNTHETIC_CLINICAL_VALUE"
            )
            assert (
                "SYNTHETIC_CLINICAL_VALUE"
                not in session.get(ClinicalRecord, result["id"]).dados_cifrados
            )
        barrier = Barrier(2)

        def concurrent_change(deactivate):
            barrier.wait(timeout=10)
            try:
                with Session(engine) as session, session.begin():
                    session.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
                    session.execute(text("SET LOCAL lock_timeout = '5s'"))
                    repository = SqlStaffRepository(session)
                    if deactivate:
                        data = {
                            key: value
                            for key, value in staff.items()
                            if key in StaffInput.model_fields
                        }
                        repository.save(
                            StaffInput(**{**data, "versao": 1, "ativo": False}),
                            professional,
                            staff["id"],
                        )
                    else:
                        repository.assign(
                            created["id"],
                            AssignmentUpdate(
                                versao=1,
                                acao_versao=2,
                                profissional_versao=1,
                                ativo=True,
                                locais_indices=[0],
                            ),
                            professional,
                            assignment["id"],
                        )
                return 200
            except HTTPException as error:
                return error.status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(concurrent_change, [False, True]))
        assert all(status in {200, 409} for status in outcomes)
        with Session(engine) as session:
            assert not session.get(StaffRecord, staff["id"]).ativo
            assert not session.get(StaffAssignment, assignment["id"]).ativo
        for table in (
            "acoes_map_marcas",
            "acoes_map_revisoes_institucionais",
            "acoes_map_profissionais_historico",
            "acoes_map_fichas_clinicas_versoes",
            "acoes_map_instituicoes",
            "acoes_map_instituicoes_marcas",
        ):
            for operation in ("DELETE", "UPDATE"):
                with engine.begin() as connection:
                    connection.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
                    try:
                        statement = (
                            f"DELETE FROM actions_map.{table}"
                            if operation == "DELETE"
                            else f"UPDATE actions_map.{table} SET id=id"
                            if table not in {"acoes_map_revisoes_institucionais"}
                            else f"UPDATE actions_map.{table} SET versao=versao"
                        )
                        connection.execute(text(statement))
                    except DBAPIError as error:
                        assert getattr(error.orig, "sqlstate", None) == "42501"
                    else:
                        raise AssertionError("Runtime não deve alterar histórico/marcas.")
                    connection.rollback()
        os.environ["OPERATIONAL_ACCESS_ENABLED"] = "true"
        get_settings.cache_clear()
        with Session(engine) as session, session.begin():
            session.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
            reception = SqlStaffRepository(session).save(
                StaffInput(nome="Recepção local sintética", categoria="RECEPCAO"),
                professional,
            )
            account = save_account(
                session,
                reception["id"],
                OperationalAccountInput(
                    usuario="recepcao.pg",
                    nova_senha="Sintetica-Postgres-2026!",
                    senha_institucional="Somente-validacao-de-DTO",
                ),
                professional,
            )
            assert account["versao"] == 1
            reset = save_account(
                session,
                reception["id"],
                OperationalAccountInput(
                    usuario="recepcao.pg",
                    versao=1,
                    ativo=False,
                    senha_institucional="Somente-validacao-de-DTO",
                ),
                professional,
            )
            assert reset["versao"] == 2 and not reset["ativo"]
        for sql in [
            "DELETE FROM actions_map.acoes_map_contas_operacionais",
            "UPDATE actions_map.acoes_map_contas_operacionais SET profissional_id=profissional_id",
            "UPDATE actions_map.acoes_map_sessoes_operacionais SET expires_at=expires_at",
        ]:
            with engine.begin() as connection:
                connection.execute(text("SET LOCAL ROLE ac_actions_map_runtime"))
                try:
                    connection.execute(text(sql))
                except DBAPIError as error:
                    assert getattr(error.orig, "sqlstate", None) == "42501"
                else:
                    raise AssertionError("Privilégio operacional excessivo.")
                connection.rollback()
        print(
            "POSTGRES_INSTITUTIONAL_OK: revisões 0007–0011 idempotentes, contas/reset, CRUD/CAS, escopo, clínica cifrada, revogação concorrente e grants mínimos."
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
        if isinstance(error, RuntimeError) and str(error).startswith("Falha no executável local "):
            print(str(error))
        raise SystemExit(1) from None
