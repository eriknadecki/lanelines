import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://lanelines:lanelines@localhost:5432/lanelines"
    jwt_secret: str = "change-me-in-production-to-a-random-32-byte-value"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    starting_balance_cents: int = 1_000_000
    # NoDecode: pydantic-settings otherwise tries to JSON-decode any list[str]
    # env var itself *before* our validator below ever runs, and raises a
    # hard SettingsError on a plain comma-separated string instead of
    # falling through to it. This crashed the app in production (a real
    # config value from a real env var), even though direct-kwarg unit
    # tests of the validator passed — those never exercised this code path.
    cors_allow_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, value: str) -> str:
        # Managed Postgres providers (Fly, Heroku, etc.) hand out plain
        # postgres:// / postgresql:// URLs; SQLAlchemy needs the driver
        # named explicitly to use psycopg3 instead of guessing psycopg2.
        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value[len("postgres://") :]
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value[len("postgresql://") :]
        return value

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _parse_origins(cls, value: object) -> object:
        # Accept either a JSON array string or a plain comma-separated string
        # (easier to type as a single platform secret/env var), handled
        # explicitly here rather than relying on pydantic-settings' env-source
        # JSON auto-parsing, which only kicks in for values actually read
        # from the environment — not for values passed directly as kwargs.
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value


settings = Settings()
