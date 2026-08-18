import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email_verification_token import (
    EmailVerificationToken,
)
from app.repositories.user_repository import UserRepository
from app.services.email_verification_service import (
    create_email_verification_token,
)

REGISTRATION_DATA = {
    "full_name": "Career Saathi",
    "email": "candidate@example.com",
    "password": "StrongPassword123!",
}

RESEND_MESSAGE = (
    "If an unverified account exists for this email, "
    "a verification message will be sent."
)


def test_registration_creates_verification_token(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    user = UserRepository(db_session).get_by_email("candidate@example.com")

    assert response.status_code == status.HTTP_201_CREATED
    assert user is not None

    statement = select(EmailVerificationToken).where(
        EmailVerificationToken.user_id == user.id
    )

    verification_tokens = list(db_session.scalars(statement))

    assert len(verification_tokens) == 1
    assert verification_tokens[0].used_at is None


def test_verify_candidate_email(
    client: TestClient,
    db_session: Session,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    user = UserRepository(db_session).get_by_email("candidate@example.com")

    assert user is not None

    _, raw_token = create_email_verification_token(
        db_session,
        user.id,
    )

    response = client.post(
        "/api/v1/auth/verify-email",
        json={"token": raw_token},
    )

    assert response.status_code == status.HTTP_200_OK

    payload = response.json()

    assert payload["success"] is True
    assert payload["message"] == ("Email verified successfully.")
    assert payload["data"]["email"] == ("candidate@example.com")
    assert payload["data"]["is_verified"] is True


def test_verify_email_rejects_reused_token(
    client: TestClient,
    db_session: Session,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    user = UserRepository(db_session).get_by_email("candidate@example.com")

    assert user is not None

    _, raw_token = create_email_verification_token(
        db_session,
        user.id,
    )

    first_response = client.post(
        "/api/v1/auth/verify-email",
        json={"token": raw_token},
    )

    second_response = client.post(
        "/api/v1/auth/verify-email",
        json={"token": raw_token},
    )

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == (status.HTTP_400_BAD_REQUEST)
    assert second_response.json()["detail"] == (
        "Invalid or expired email verification token."
    )


def test_verify_email_rejects_unknown_token(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/verify-email",
        json={"token": "x" * 43},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == ("Invalid or expired email verification token.")


def test_resend_verification_invalidates_old_token(
    client: TestClient,
    db_session: Session,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    user = UserRepository(db_session).get_by_email("candidate@example.com")

    assert user is not None

    statement = (
        select(EmailVerificationToken)
        .where(EmailVerificationToken.user_id == user.id)
        .order_by(EmailVerificationToken.created_at)
    )

    original_token = db_session.scalars(statement).first()

    assert original_token is not None
    assert original_token.used_at is None

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "candidate@example.com"},
    )

    db_session.refresh(original_token)

    verification_tokens = list(db_session.scalars(statement))

    active_tokens = [token for token in verification_tokens if token.used_at is None]

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "success": True,
        "message": RESEND_MESSAGE,
    }
    assert original_token.used_at is not None
    assert len(verification_tokens) == 2
    assert len(active_tokens) == 1


def test_resend_verification_uses_generic_response(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "success": True,
        "message": RESEND_MESSAGE,
    }


def test_registration_schedules_verification_email(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_emails: list[tuple[str, str, str]] = []

    def fake_send_verification_email(
        recipient_email: str,
        recipient_name: str,
        raw_verification_token: str,
    ) -> None:
        sent_emails.append(
            (
                recipient_email,
                recipient_name,
                raw_verification_token,
            )
        )

    monkeypatch.setattr(
        "app.api.routes.auth.send_verification_email",
        fake_send_verification_email,
    )

    response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert len(sent_emails) == 1
    assert sent_emails[0][0] == "candidate@example.com"
    assert sent_emails[0][1] == "Career Saathi"
    assert len(sent_emails[0][2]) >= 32


def test_resend_schedules_verification_email(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_emails: list[tuple[str, str, str]] = []

    def fake_send_verification_email(
        recipient_email: str,
        recipient_name: str,
        raw_verification_token: str,
    ) -> None:
        sent_emails.append(
            (
                recipient_email,
                recipient_name,
                raw_verification_token,
            )
        )

    monkeypatch.setattr(
        "app.api.routes.auth.send_verification_email",
        fake_send_verification_email,
    )

    registration_response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    assert registration_response.status_code == (status.HTTP_201_CREATED)

    sent_emails.clear()

    resend_response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "candidate@example.com"},
    )

    assert resend_response.status_code == status.HTTP_200_OK
    assert len(sent_emails) == 1
    assert sent_emails[0][0] == "candidate@example.com"
    assert sent_emails[0][1] == "Career Saathi"
    assert len(sent_emails[0][2]) >= 32
