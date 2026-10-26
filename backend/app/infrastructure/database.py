from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import get_settings


def institutional_engine(url: str) -> Engine:
    url = url.replace("postgres://", "postgresql+psycopg://", 1).replace(
        "postgresql://", "postgresql+psycopg://", 1
    )
    return create_engine(
        url, hide_parameters=True, pool_pre_ping=True, connect_args={"connect_timeout": 8}
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
    if url.startswith("sqlite:"):
        if config.production:
            raise RuntimeError("Produção exige persistência institucional revisada.")
        if ":memory:" not in url:
            Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(url, connect_args={"check_same_thread": False}, hide_parameters=True)
        # Apenas o armazenamento SQLite isolado de desenvolvimento é inicializado.
        from app.infrastructure.models import Base

        Base.metadata.create_all(engine)
        return engine
    raise RuntimeError("Persistência PostgreSQL do módulo aguarda revisão e migração aprovada.")
