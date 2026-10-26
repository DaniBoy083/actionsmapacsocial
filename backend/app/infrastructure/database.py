from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.pool import NullPool

from app.config import get_settings


def institutional_engine(url: str) -> Engine:
    url = url.replace("postgres://", "postgresql+psycopg://", 1).replace(
        "postgresql://", "postgresql+psycopg://", 1
    )
    return create_engine(
        url,
        hide_parameters=True,
        pool_pre_ping=True,
        poolclass=NullPool,
        connect_args={"connect_timeout": 8},
    )


@lru_cache
def get_identity_engine() -> Engine:
    url = get_settings().database_url.get_secret_value()
    if not url:
        raise RuntimeError("CONFIG_AUSENTE")
    return institutional_engine(url)


@lru_cache
def get_engine() -> Engine:
    config = get_settings()
    url = config.actions_storage_url
    if config.production:
        url = config.database_url.get_secret_value()
        parsed = make_url(url)
        if parsed.drivername not in {
            "postgres",
            "postgresql",
            "postgresql+psycopg",
        } or parsed.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}:
            raise RuntimeError("Produção exige PostgreSQL com TLS.")
        # Schema isolado; nunca cria tabelas no startup ou modifica a identidade institucional.
        return institutional_engine(url).execution_options(
            schema_translate_map={None: "actions_map"}
        )
    if url.startswith("sqlite:"):
        if ":memory:" not in url:
            Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(url, connect_args={"check_same_thread": False}, hide_parameters=True)
        # Apenas o armazenamento SQLite isolado de desenvolvimento é inicializado.
        from app.infrastructure.models import Base

        Base.metadata.create_all(engine)
        return engine
    raise RuntimeError("Persistência PostgreSQL do módulo aguarda revisão e migração aprovada.")
