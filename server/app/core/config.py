from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIRECTORY = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "CareerSaathi AI API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    client_url: str = "http://localhost:5173"
    google_client_id: str | None = None

    jwt_secret_key: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    email_verification_token_expire_hours: int = 24
    email_delivery_enabled: bool = False
    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_username: SecretStr | None = None
    smtp_password: SecretStr | None = None
    smtp_use_tls: bool = True
    email_from_name: str = "CareerSaathi AI"
    email_from_address: str = "no-reply@example.com"

    refresh_cookie_name: str = "careersaathi_refresh_token"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal[
        "lax",
        "strict",
        "none",
    ] = "lax"

    postgres_user: str
    postgres_password: SecretStr
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "careersaathi_ai"

    model_config = SettingsConfigDict(
        env_file=SERVER_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
