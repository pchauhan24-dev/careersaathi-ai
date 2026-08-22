from functools import lru_cache
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import (
    Field,
    SecretStr,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIRECTORY = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "CareerSaathi AI API"
    app_version: str = "0.1.0"
    environment: Literal[
        "development",
        "test",
        "production",
    ] = "development"
    api_v1_prefix: str = "/api/v1"
    client_url: str = "http://localhost:5173"

    api_docs_enabled: bool = True
    trusted_hosts: str = "localhost,127.0.0.1,testserver"

    rate_limit_enabled: bool = True
    rate_limit_storage_uri: SecretStr = SecretStr("memory://")

    google_client_id: str | None = None

    github_client_id: str | None = None
    github_client_secret: SecretStr | None = None
    github_redirect_uri: str = "http://localhost:8000/api/v1/auth/github/callback"

    jwt_secret_key: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=90,
    )

    email_verification_token_expire_hours: int = Field(
        default=24,
        ge=1,
        le=168,
    )
    password_reset_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=120,
    )

    email_delivery_enabled: bool = False
    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = Field(
        default=587,
        ge=1,
        le=65535,
    )
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
    postgres_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
    )
    postgres_db: str = "careersaathi_ai"

    model_config = SettingsConfigDict(
        env_file=SERVER_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def trusted_host_list(self) -> list[str]:
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]

    @model_validator(mode="after")
    def validate_security_configuration(self) -> Self:
        jwt_secret = self.jwt_secret_key.get_secret_value()

        if len(jwt_secret) < 32 or not jwt_secret.strip():
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters.")

        client_url = urlparse(self.client_url)

        if client_url.scheme not in {"http", "https"} or not client_url.netloc:
            raise ValueError("CLIENT_URL must be a valid HTTP or HTTPS URL.")

        trusted_hosts = self.trusted_host_list

        if not trusted_hosts:
            raise ValueError("TRUSTED_HOSTS must contain at least one host.")

        for trusted_host in trusted_hosts:
            if "://" in trusted_host or "/" in trusted_host or " " in trusted_host:
                raise ValueError("TRUSTED_HOSTS must contain hostnames only.")

        rate_limit_storage_uri = self.rate_limit_storage_uri.get_secret_value().strip()
        rate_limit_storage = urlparse(rate_limit_storage_uri)

        if rate_limit_storage.scheme not in {
            "memory",
            "redis",
            "rediss",
        }:
            raise ValueError(
                "RATE_LIMIT_STORAGE_URI must use memory://, redis://, or rediss://."
            )

        if (
            rate_limit_storage.scheme in {"redis", "rediss"}
            and not rate_limit_storage.netloc
        ):
            raise ValueError("Redis rate-limit storage must include a host.")

        github_client_id = (self.github_client_id or "").strip()
        github_client_secret = (
            self.github_client_secret.get_secret_value().strip()
            if self.github_client_secret is not None
            else ""
        )

        if bool(github_client_id) != bool(github_client_secret):
            raise ValueError(
                "GitHub client ID and client secret must be configured together."
            )

        if github_client_id:
            github_redirect_uri = urlparse(self.github_redirect_uri)

            if (
                github_redirect_uri.scheme not in {"http", "https"}
                or not github_redirect_uri.netloc
            ):
                raise ValueError(
                    "GITHUB_REDIRECT_URI must be a valid HTTP or HTTPS URL."
                )

        smtp_username = (
            self.smtp_username.get_secret_value().strip()
            if self.smtp_username is not None
            else ""
        )
        smtp_password = (
            self.smtp_password.get_secret_value().strip()
            if self.smtp_password is not None
            else ""
        )

        if bool(smtp_username) != bool(smtp_password):
            raise ValueError("SMTP username and password must be configured together.")

        if self.email_delivery_enabled and not (smtp_username and smtp_password):
            raise ValueError(
                "SMTP credentials are required when email delivery is enabled."
            )

        if self.refresh_cookie_samesite == "none" and not self.refresh_cookie_secure:
            raise ValueError("SameSite=None requires a secure refresh cookie.")

        if self.environment == "production":
            if client_url.scheme != "https":
                raise ValueError("Production CLIENT_URL must use HTTPS.")

            if not self.refresh_cookie_secure:
                raise ValueError("Production refresh cookies must be secure.")

            if self.api_docs_enabled:
                raise ValueError("API documentation must be disabled in production.")

            if any("*" in host for host in trusted_hosts):
                raise ValueError(
                    "Wildcard trusted hosts are not allowed in production."
                )

            if not self.rate_limit_enabled:
                raise ValueError("Rate limiting must be enabled in production.")

            if rate_limit_storage.scheme == "memory":
                raise ValueError(
                    "Production rate limiting requires external Redis storage."
                )

            if github_client_id:
                github_redirect_uri = urlparse(self.github_redirect_uri)

                if github_redirect_uri.scheme != "https":
                    raise ValueError("Production GitHub redirect URI must use HTTPS.")

            if self.email_delivery_enabled and not self.smtp_use_tls:
                raise ValueError("Production SMTP delivery must use TLS.")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
