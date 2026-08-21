import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings

REGISTRATION_DATA = {
    "full_name": "Career Saathi",
    "email": "candidate@example.com",
    "password": "StrongPassword123!",
}

FORGOT_PASSWORD_MESSAGE = (
    "If an active account exists for this email, a password reset message will be sent."
)


def install_reset_email_spy(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, str, str]]:
    sent_emails: list[tuple[str, str, str]] = []

    def fake_send_password_reset_email(
        recipient_email: str,
        recipient_name: str,
        raw_reset_token: str,
    ) -> None:
        sent_emails.append(
            (
                recipient_email,
                recipient_name,
                raw_reset_token,
            )
        )

    monkeypatch.setattr(
        "app.api.routes.auth.send_password_reset_email",
        fake_send_password_reset_email,
    )

    return sent_emails


def test_forgot_password_schedules_reset_email(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_emails = install_reset_email_spy(monkeypatch)

    client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "candidate@example.com"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "success": True,
        "message": FORGOT_PASSWORD_MESSAGE,
    }

    assert len(sent_emails) == 1
    assert sent_emails[0][0] == "candidate@example.com"
    assert sent_emails[0][1] == "Career Saathi"
    assert len(sent_emails[0][2]) >= 32


def test_forgot_password_uses_generic_unknown_email_response(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_emails = install_reset_email_spy(monkeypatch)

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "success": True,
        "message": FORGOT_PASSWORD_MESSAGE,
    }
    assert sent_emails == []


def test_reset_password(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_emails = install_reset_email_spy(monkeypatch)

    client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "candidate@example.com"},
    )

    raw_reset_token = sent_emails[0][2]

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": raw_reset_token,
            "new_password": "NewStrongPassword456!",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "success": True,
        "message": ("Password reset successfully. Please log in again."),
    }

    set_cookie_header = response.headers["set-cookie"]

    assert f"{settings.refresh_cookie_name}=" in set_cookie_header
    assert "Max-Age=0" in set_cookie_header

    old_login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "candidate@example.com",
            "password": "StrongPassword123!",
        },
    )

    new_login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "candidate@example.com",
            "password": "NewStrongPassword456!",
        },
    )

    assert old_login_response.status_code == (status.HTTP_401_UNAUTHORIZED)
    assert new_login_response.status_code == status.HTTP_200_OK


def test_reset_password_rejects_reused_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_emails = install_reset_email_spy(monkeypatch)

    client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "candidate@example.com"},
    )

    raw_reset_token = sent_emails[0][2]

    first_response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": raw_reset_token,
            "new_password": "NewStrongPassword456!",
        },
    )

    second_response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": raw_reset_token,
            "new_password": "AnotherStrongPassword789!",
        },
    )

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == (status.HTTP_400_BAD_REQUEST)
    assert second_response.json()["detail"] == (
        "Invalid or expired password reset token."
    )


def test_reset_password_rejects_unknown_token(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "x" * 43,
            "new_password": "NewStrongPassword456!",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == ("Invalid or expired password reset token.")


def test_reset_password_rejects_invalid_request_data(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "short",
            "new_password": "short",
        },
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)
