"""Read-only discovery: prints schema metadata, never credentials or row values."""

import json
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

root = Path(__file__).resolve().parents[1]
config = {**dotenv_values(root / ".env"), **dotenv_values(root / ".env.local")}
url = config.get("DATABASE_URL_UNPOOLED") or config.get("DATABASE_URL")
if not url:
    print("CONFIG_AUSENTE")
    sys.exit(1)
url = url.replace("postgres://", "postgresql+psycopg://", 1).replace(
    "postgresql://", "postgresql+psycopg://", 1
)
try:
    engine = create_engine(url, connect_args={"connect_timeout": 8}, hide_parameters=True)
    with engine.connect() as conn, conn.begin():
        conn.execute(text("SET TRANSACTION READ ONLY"))
        conn.execute(text("SET LOCAL statement_timeout = '8s'"))
        assert conn.scalar(text("SELECT 1")) == 1
        rows = (
            conn.execute(
                text("""
            SELECT table_schema, table_name, column_name, data_type
            FROM information_schema.columns
            WHERE (table_schema = 'public' AND table_name IN
              ('profissionais_cadastrados', 'equipes_profissionais'))
               OR (table_schema = 'portal' AND table_name IN
              ('institutional_actions', 'beneficiaries'))
            ORDER BY table_schema, table_name, ordinal_position
        """)
            )
            .mappings()
            .all()
        )
        print("DB_OK")
        print(json.dumps([dict(row) for row in rows]))
except (SQLAlchemyError, OSError, ValueError):
    print("DB_ERRO: descoberta indisponivel; nenhum dado foi alterado.")
    sys.exit(1)
