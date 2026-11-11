"""Migrações administrativas do armazenamento SQLite de desenvolvimento."""

from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from cryptography.fernet import Fernet
from sqlalchemy import JSON, Column, DateTime, inspect, select
from sqlalchemy.engine import Engine

from app.infrastructure.models import (
    Action,
    ActionLogo,
    InstitutionalRevision,
    IntegrationCredential,
    Participation,
)


def add_local_institutional_metadata(
    engine: Engine,
    key: str,
    backup_directory: Path,
    *,
    apply: bool = False,
) -> bool:
    """Migração local explícita e idempotente, com backup anterior ao DDL."""
    if engine.dialect.name != "sqlite":
        raise ValueError("Procedimento exclusivo do SQLite local.")
    with engine.begin() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        inspector = inspect(connection)
        additions = [
            (
                Action.__tablename__,
                Column("institucional", JSON, nullable=False, server_default="{}"),
            ),
            (Participation.__tablename__, Column("documento_institucional", JSON, nullable=True)),
        ]
        missing = [
            (table, column)
            for table, column in additions
            if inspector.has_table(table)
            and column.name not in {item["name"] for item in inspector.get_columns(table)}
        ]
        new_tables = [
            table
            for table in (ActionLogo.__table__, InstitutionalRevision.__table__)
            if not inspector.has_table(table.name)
        ]
        if not missing and not new_tables or not apply:
            return False
        plaintext = connection.connection.driver_connection.serialize()
        cipher = Fernet(key.encode())
        backup_directory.mkdir(parents=True, exist_ok=True)
        destination = backup_directory / ("sqlite-institucional-" + str(uuid4()) + ".fernet")
        with destination.open("xb") as stream:
            stream.write(cipher.encrypt(plaintext))
        if cipher.decrypt(destination.read_bytes()) != plaintext:
            raise RuntimeError("Backup SQLite não verificado.")
        operations = Operations(MigrationContext.configure(connection))
        for table, column in missing:
            operations.add_column(table, column)
        for table in new_tables:
            table.create(connection, checkfirst=True)
    return True


def allow_nonexpiring_local_tokens(
    engine: Engine,
    key: str,
    backup_directory: Path,
    *,
    apply: bool = False,
) -> bool:
    if engine.dialect.name != "sqlite":
        raise ValueError("Procedimento exclusivo do SQLite local.")
    table = IntegrationCredential.__table__
    with engine.begin() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        if not inspect(connection).has_table(table.name):
            return False  # Um armazenamento novo receberá o modelo atual no startup local.
        columns = inspect(connection).get_columns(table.name)
        if next(column for column in columns if column["name"] == "expira_em")["nullable"]:
            return False
        if not apply:
            return False
        before = connection.execute(select(table).order_by(table.c.id)).all()
        plaintext = connection.connection.driver_connection.serialize()
        cipher = Fernet(key.encode())
        encrypted = cipher.encrypt(plaintext)
        backup_directory.mkdir(parents=True, exist_ok=True)
        destination = backup_directory / ("sqlite-tokens-" + str(uuid4()) + ".fernet")
        with destination.open("xb") as stream:
            stream.write(encrypted)
        if cipher.decrypt(destination.read_bytes()) != plaintext:
            raise RuntimeError("Backup SQLite não verificado.")
        operations = Operations(MigrationContext.configure(connection))
        with operations.batch_alter_table(table.name) as batch:
            batch.alter_column("expira_em", existing_type=DateTime(timezone=True), nullable=True)
        if before != connection.execute(select(table).order_by(table.c.id)).all():
            raise RuntimeError("Credenciais existentes divergiram após a migração local.")
    return True
