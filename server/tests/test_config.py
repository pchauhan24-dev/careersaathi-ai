import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings

BASE_SETTINGS = {
    "environment": "development",
    "jwt_secret_key": SecretStr("x" * 32),
    "postgres_user": "test-user",
    "postgres_password": SecretStr("test-password"),
    "postgres_db": "test-database",
}


def create_settings(**overrides) -> Settings:
    values = {
        **BASE_SETTINGS,
        **overrides,
    }

    return Settings(
        _env_file=None,
        **values,
    )


def test_settings_accept_secure_development_configuration() -> None:
    application_settings = create_settings()

    assert application_settings.environment == "development"
    assert application_settings.refresh_cookie_secure is False
    assert application_settings.refresh_cookie_samesite == "lax"
    assert application_settings.api_docs_enabled is True
    assert application_settings.trusted_host_list == [
        "localhost",
        "127.0.0.1",
        "testserver",
    ]
    assert application_settings.rate_limit_enabled is True
    assert application_settings.rate_limit_storage_uri.get_secret_value() == "memory://"


def test_settings_reject_short_jwt_secret() -> None:
    with pytest.raises(
        ValidationError,
        match="JWT_SECRET_KEY must contain at least 32 characters",
    ):
        create_settings(
            jwt_secret_key=SecretStr("too-short"),
        )


def test_settings_reject_insecure_samesite_none_cookie() -> None:
    with pytest.raises(
        ValidationError,
        match="SameSite=None requires a secure refresh cookie",
    ):
        create_settings(
            refresh_cookie_samesite="none",
            refresh_cookie_secure=False,
        )


def test_settings_require_paired_github_credentials() -> None:
    with pytest.raises(
        ValidationError,
        match="GitHub client ID and client secret must be configured together",
    ):
        create_settings(
            github_client_id="github-client-id",
            github_client_secret=None,
        )


def test_settings_require_smtp_credentials_when_enabled() -> None:
    with pytest.raises(
        ValidationError,
        match="SMTP credentials are required when email delivery is enabled",
    ):
        create_settings(
            email_delivery_enabled=True,
            smtp_username=None,
            smtp_password=None,
        )


def test_settings_reject_unsupported_rate_limit_storage() -> None:
    with pytest.raises(
        ValidationError,
        match="RATE_LIMIT_STORAGE_URI must use",
    ):
        create_settings(
            rate_limit_storage_uri=SecretStr("sqlite:///rate-limits.db"),
        )


def test_settings_reject_redis_storage_without_host() -> None:
    with pytest.raises(
        ValidationError,
        match="Redis rate-limit storage must include a host",
    ):
        create_settings(
            rate_limit_storage_uri=SecretStr("redis://"),
        )


def test_production_settings_require_https_and_secure_cookie() -> None:
    production_rate_limit_storage = SecretStr("rediss://redis.example.com:6379/0")

    with pytest.raises(
        ValidationError,
        match="Production CLIENT_URL must use HTTPS",
    ):
        create_settings(
            environment="production",
            client_url="http://example.com",
            refresh_cookie_secure=True,
            api_docs_enabled=False,
            trusted_hosts="example.com",
            rate_limit_storage_uri=production_rate_limit_storage,
        )

    with pytest.raises(
        ValidationError,
        match="Production refresh cookies must be secure",
    ):
        create_settings(
            environment="production",
            client_url="https://example.com",
            refresh_cookie_secure=False,
            api_docs_enabled=False,
            trusted_hosts="example.com",
            rate_limit_storage_uri=production_rate_limit_storage,
        )


def test_production_settings_require_rate_limiting() -> None:
    with pytest.raises(
        ValidationError,
        match="Rate limiting must be enabled in production",
    ):
        create_settings(
            environment="production",
            client_url="https://example.com",
            refresh_cookie_secure=True,
            api_docs_enabled=False,
            trusted_hosts="example.com",
            rate_limit_enabled=False,
            rate_limit_storage_uri=SecretStr("rediss://redis.example.com:6379/0"),
        )


def test_production_settings_reject_memory_rate_limit_storage() -> None:
    with pytest.raises(
        ValidationError,
        match=("Production rate limiting requires external Redis storage"),
    ):
        create_settings(
            environment="production",
            client_url="https://example.com",
            refresh_cookie_secure=True,
            api_docs_enabled=False,
            trusted_hosts="example.com",
            rate_limit_storage_uri=SecretStr("memory://"),
        )


def test_settings_accept_secure_production_configuration() -> None:
    application_settings = create_settings(
        environment="production",
        client_url="https://careersaathi.example.com",
        refresh_cookie_secure=True,
        api_docs_enabled=False,
        trusted_hosts="careersaathi.example.com",
        rate_limit_storage_uri=SecretStr("rediss://redis.example.com:6379/0"),
    )

    assert application_settings.environment == "production"
    assert application_settings.refresh_cookie_secure is True
    assert application_settings.api_docs_enabled is False
    assert application_settings.rate_limit_enabled is True
    assert application_settings.trusted_host_list == ["careersaathi.example.com"]


def test_settings_reject_invalid_trusted_hosts() -> None:
    with pytest.raises(
        ValidationError,
        match="TRUSTED_HOSTS must contain at least one host",
    ):
        create_settings(
            trusted_hosts=" , ",
        )

    with pytest.raises(
        ValidationError,
        match="TRUSTED_HOSTS must contain hostnames only",
    ):
        create_settings(
            trusted_hosts="https://example.com",
        )


def test_production_settings_require_disabled_api_docs() -> None:
    with pytest.raises(
        ValidationError,
        match="API documentation must be disabled in production",
    ):
        create_settings(
            environment="production",
            client_url="https://example.com",
            refresh_cookie_secure=True,
            api_docs_enabled=True,
            trusted_hosts="example.com",
            rate_limit_storage_uri=SecretStr("rediss://redis.example.com:6379/0"),
        )


def test_production_settings_reject_wildcard_trusted_hosts() -> None:
    with pytest.raises(
        ValidationError,
        match="Wildcard trusted hosts are not allowed in production",
    ):
        create_settings(
            environment="production",
            client_url="https://example.com",
            refresh_cookie_secure=True,
            api_docs_enabled=False,
            trusted_hosts="*",
            rate_limit_storage_uri=SecretStr("rediss://redis.example.com:6379/0"),
        )
