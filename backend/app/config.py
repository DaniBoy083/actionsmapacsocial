from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env", ROOT / ".env.local"),
        extra="ignore",
    )
    app_env: str = "development"
    database_url: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices(
            "ACTIONS_DATABASE_URL", "DATABASE_URL", "POSTGRES_DATABASE_URL", "POSTGRES_URL"
        ),
    )
    actions_storage_url: str = "sqlite:///" + (ROOT / "backend/private/actions.sqlite3").as_posix()
    session_secret: SecretStr = SecretStr("")
    beneficiaries_key: SecretStr = SecretStr("")
    frontend_origin: str = "http://localhost:3000"
    agenda_web_url: str = ""
    agenda_summaries_url: str = ""
    agenda_service_token: SecretStr = SecretStr("")
    consolidated_analytics_api_base_url: str = ""
    consolidated_analytics_api_token: SecretStr = SecretStr("")

    @property
    def production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
