from email.message import EmailMessage
from typing import Any

import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.core.exceptions import EmailDeliveryError
from app.services.email_service import (
    build_email_verification_url,
    build_password_reset_email,
    build_password_reset_url,
    send_password_reset_email,
    send_verification_email,
)


class FakeSMTP:
    instances: list["FakeSMTP"] = []

    def __init__(
        self,
        host: str,
        port: int,
        timeout: int,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_credentials: tuple[str, str] | None = None
        self.sent_message: EmailMessage | None = None

        self.instances.append(self)

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        return None

    def ehlo(self) -> None:
        return None

    def starttls(self, *, context: Any) -> None:
        self.started_tls = True

    def login(
        self,
        username: str,
        password: str,
    ) -> None:
        self.login_credentials = (username, password)

    def send_message(
        self,
        message: EmailMessage,
    ) -> None:
        self.sent_message = message


def test_build_email_verification_url() -> None:
    url = build_email_verification_url("test-verification-token")

    assert url == (f"{settings.client_url}/verify-email?token=test-verification-token")


def test_send_verification_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeSMTP.instances.clear()

    monkeypatch.setattr(
        settings,
        "email_delivery_enabled",
        True,
    )
    monkeypatch.setattr(
        settings,
        "smtp_username",
        SecretStr("test-smtp-user"),
    )
    monkeypatch.setattr(
        settings,
        "smtp_password",
        SecretStr("test-smtp-password"),
    )
    monkeypatch.setattr(
        "app.services.email_service.smtplib.SMTP",
        FakeSMTP,
    )

    send_verification_email(
        "candidate@example.com",
        "Career Saathi",
        "test-verification-token",
    )

    smtp = FakeSMTP.instances[0]

    assert smtp.host == settings.smtp_host
    assert smtp.port == settings.smtp_port
    assert smtp.timeout == 15
    assert smtp.started_tls is True
    assert smtp.login_credentials == (
        "test-smtp-user",
        "test-smtp-password",
    )
    assert smtp.sent_message is not None
    assert smtp.sent_message["To"] == ("candidate@example.com")
    assert smtp.sent_message["Subject"] == ("Verify your CareerSaathi AI email")


def test_disabled_email_delivery_does_not_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("SMTP should not be called.")

    monkeypatch.setattr(
        settings,
        "email_delivery_enabled",
        False,
    )
    monkeypatch.setattr(
        "app.services.email_service.smtplib.SMTP",
        fail_if_called,
    )

    send_verification_email(
        "candidate@example.com",
        "Career Saathi",
        "test-verification-token",
    )


def test_missing_smtp_credentials_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "email_delivery_enabled",
        True,
    )
    monkeypatch.setattr(
        settings,
        "smtp_username",
        None,
    )
    monkeypatch.setattr(
        settings,
        "smtp_password",
        None,
    )

    with pytest.raises(EmailDeliveryError):
        send_verification_email(
            "candidate@example.com",
            "Career Saathi",
            "test-verification-token",
        )


def test_build_password_reset_url() -> None:
    url = build_password_reset_url("test-reset-token")

    assert url == (f"{settings.client_url}/reset-password?token=test-reset-token")


def test_build_password_reset_email() -> None:
    message = build_password_reset_email(
        "candidate@example.com",
        "Career Saathi",
        "test-reset-token",
    )

    message_content = message.as_string()

    assert message["To"] == "candidate@example.com"
    assert message["Subject"] == ("Reset your CareerSaathi AI password")
    assert "test-reset-token" in message_content
    assert str(settings.password_reset_token_expire_minutes) in (message_content)


def test_send_password_reset_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeSMTP.instances.clear()

    monkeypatch.setattr(
        settings,
        "email_delivery_enabled",
        True,
    )
    monkeypatch.setattr(
        settings,
        "smtp_username",
        SecretStr("test-smtp-user"),
    )
    monkeypatch.setattr(
        settings,
        "smtp_password",
        SecretStr("test-smtp-password"),
    )
    monkeypatch.setattr(
        "app.services.email_service.smtplib.SMTP",
        FakeSMTP,
    )

    send_password_reset_email(
        "candidate@example.com",
        "Career Saathi",
        "test-reset-token",
    )

    smtp = FakeSMTP.instances[0]

    assert smtp.started_tls is True
    assert smtp.login_credentials == (
        "test-smtp-user",
        "test-smtp-password",
    )
    assert smtp.sent_message is not None
    assert smtp.sent_message["To"] == "candidate@example.com"
    assert smtp.sent_message["Subject"] == ("Reset your CareerSaathi AI password")
