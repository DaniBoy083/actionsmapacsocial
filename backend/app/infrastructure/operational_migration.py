"""Migração SQLite explícita: backup cifrado, tabelas aditivas e backfill de autoria comprovada."""

from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet
from sqlalchemy import inspect, select

from app.infrastructure.models import (
    ActionInstitution,
    ClinicalDesignation,
    ClinicalRecord,
    Institution,
    InstitutionLogo,
)

TABLES = (
    Institution.__table__,
    InstitutionLogo.__table__,
    ActionInstitution.__table__,
    ClinicalDesignation.__table__,
)


def migrate_local(engine, key: str, backup_directory: Path, *, apply=False):
    if engine.dialect.name != "sqlite":
        raise ValueError("Procedimento exclusivo do SQLite local.")
    with engine.begin() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        missing = [table for table in TABLES if not inspect(connection).has_table(table.name)]
        # Startup local pode ter criado as tabelas: ainda conferir backfill de fichas anteriores.
        pending = []
        if inspect(connection).has_table(ClinicalRecord.__tablename__):
            query = select(ClinicalRecord.__table__)
            if inspect(connection).has_table(ClinicalDesignation.__tablename__):
                query = query.where(
                    ~ClinicalRecord.participacao_id.in_(select(ClinicalDesignation.participacao_id))
                )
            pending = connection.execute(query).mappings().all()
        report = {
            "tabelas_pendentes": len(missing),
            "designacoes_pendentes": len(pending),
            "aplicado": False,
        }
        if not apply or not (missing or pending):
            return report
        cipher = Fernet(key.encode())
        raw = connection.connection.driver_connection.serialize()
        backup_directory.mkdir(parents=True, exist_ok=True)
        destination = backup_directory / f"sqlite-operacao-{uuid4()}.fernet"
        with destination.open("xb") as stream:
            stream.write(cipher.encrypt(raw))
        if cipher.decrypt(destination.read_bytes()) != raw:
            raise RuntimeError("Backup não verificado.")
        for table in missing:
            table.create(connection)
        for record in pending:
            connection.execute(
                ClinicalDesignation.__table__.insert().values(
                    participacao_id=record["participacao_id"],
                    profissional_id=record["autor_profissional_id"],
                    identidade_id=record["autor_identidade_id"],
                    versao=1,
                    ativo=True,
                    atualizado_por=record["autor_identidade_id"],
                    atualizado_em=record["atualizado_em"],
                )
            )
        report["aplicado"] = True
        return report
