import os

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema

SCHEMA = "actions_map"
config = context.config


def migrate(connection):
    connection.execute(CreateSchema(SCHEMA, if_not_exists=True))
    context.configure(
        connection=connection,
        version_table_schema=SCHEMA,
        version_table="alembic_version",
        transactional_ddl=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url="postgresql://",
        literal_binds=True,
        version_table_schema=SCHEMA,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.execute(CreateSchema(SCHEMA, if_not_exists=True))
        context.run_migrations()
elif config.attributes.get("connection") is not None:
    migrate(config.attributes["connection"])
else:
    url = os.environ.get("ACTIONS_MIGRATION_URL", "")
    if not url:
        raise RuntimeError(
            "Configure ACTIONS_MIGRATION_URL no processo administrativo de migração."
        )
    url = url.replace("postgresql://", "postgresql+psycopg://", 1).replace(
        "postgres://", "postgresql+psycopg://", 1
    )
    engine = create_engine(url, hide_parameters=True, connect_args={"connect_timeout": 8})
    with engine.connect() as connection, connection.begin():
        migrate(connection)
