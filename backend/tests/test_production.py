import json
from pathlib import Path

from app.check_deployment import check
from app.config import Settings
from app.infrastructure.models import LoginLimit
from cryptography.fernet import Fernet
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert


def test_production_gate_and_provider_aliases(monkeypatch):
    monkeypatch.setenv(
        "ACTIONS_DATABASE_URL",
        "postgresql://synthetic:synthetic@db.example.invalid/test?sslmode=require",
    )
    settings = Settings(
        _env_file=None,
        app_env="production",
        frontend_origin="https://actions.example.invalid",
        session_secret="synthetic-" * 5,
        beneficiaries_key=Fernet.generate_key().decode(),
    )
    assert all(check(settings).values())
    monkeypatch.setenv("ACTIONS_DATABASE_URL", "sqlite:///local.sqlite3")
    assert not check(Settings(_env_file=None, app_env="production"))["database_tls"]


def test_migration_is_isolated_and_has_no_seed():
    source = Path(__file__).resolve().parents[1] / "alembic/versions/0001_actions_map.sql"
    sql = source.read_text(encoding="utf-8")
    assert sql.count("CREATE TABLE actions_map.") == 8
    assert "public." not in sql
    assert "INSERT" not in sql and "DROP" not in sql and "ALTER" not in sql
    assert "REFERENCES actions_map." in sql


def test_postgres_rate_limit_uses_atomic_conflict_update():
    statement = insert(LoginLimit).values(key="synthetic", attempts=1)
    statement = statement.on_conflict_do_update(
        index_elements=[LoginLimit.key], set_={"attempts": LoginLimit.attempts + 1}
    )
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT" in sql and "attempts + " in sql


def test_backend_remains_private_and_frontend_has_binding():
    config = json.loads((Path(__file__).resolve().parents[2] / "vercel.json").read_text())
    assert config["services"]["frontend"]["framework"] == "nextjs"
    assert config["services"]["backend"]["framework"] == "fastapi"
    assert config["services"]["frontend"]["bindings"][0]["env"] == "ACTIONS_BACKEND_URL"
    assert [
        item["source"] for item in config["rewrites"] if item["destination"]["service"] == "backend"
    ] == ["/api/v1/health"]
