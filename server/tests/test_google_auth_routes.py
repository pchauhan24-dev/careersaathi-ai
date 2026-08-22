import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    GoogleAuthenticationConfigurationError,
    InvalidGoogleCredentialError,
)
from app.core.security import decode_access_token, hash_password
from app.models.social_account import GOOGLE_PROVIDER
from app.repositories.social_account_repository import (
    SocialAccountRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.google_identity_service import GoogleIdentity

GOOGLE_CREDENTIAL = "x" * 100


def mock_google_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    subject: str = "google-user-123",
    email: str = "candidate@example.com",
    full_name: str = "Career Saathi",
) -> None:
    identity = GoogleIdentity(
        subject=subject,
        email=email,
        full_name=full_name,
    )

    monkeypatch.setattr(
        "app.services.google_auth_service.verify_google_credential",
        lambda credential: identity,
    )


def test_google_login_creates_authenticated_user(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_google_identity(monkeypatch)

    response = client.post(
        "/api/v1/auth/google",
        json={"credential": GOOGLE_CREDENTIAL},
    )

    assert response.status_code == status.HTTP_200_OK

    payload = response.json()
    user = UserRepository(db_session).get_by_email("candidate@example.com")

    assert user is not None

    social_account = SocialAccountRepository(db_session).get_by_provider_subject(
        GOOGLE_PROVIDER,
        "google-user-123",
    )

    refresh_cookie = response.cookies.get(settings.refresh_cookie_name)
    token_payload = decode_access_token(payload["data"]["access_token"])

    assert payload["success"] is True
    assert payload["message"] == "Google login successful."
    assert payload["data"]["token_type"] == "bearer"
    assert payload["data"]["expires_in"] == 1800
    assert payload["data"]["user"]["id"] == str(user.id)

    assert user.password_hash is None
    assert user.is_verified is True

    assert social_account is not None
    assert social_account.user_id == user.id

    assert refresh_cookie is not None
    assert token_payload["sub"] == str(user.id)


def test_google_login_returns_existing_google_user(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_google_identity(monkeypatch)

    first_response = client.post(
        "/api/v1/auth/google",
        json={"credential": GOOGLE_CREDENTIAL},
    )
    second_response = client.post(
        "/api/v1/auth/google",
        json={"credential": GOOGLE_CREDENTIAL},
    )

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK

    first_user_id = first_response.json()["data"]["user"]["id"]
    second_user_id = second_response.json()["data"]["user"]["id"]

    user = UserRepository(db_session).get_by_email("candidate@example.com")

    assert user is not None

    social_accounts = SocialAccountRepository(db_session).list_by_user(user.id)

    assert first_user_id == second_user_id
    assert len(social_accounts) == 1


def test_google_login_rejects_invalid_credential(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_google_credential(
        credential: str,
    ) -> GoogleIdentity:
        raise InvalidGoogleCredentialError

    monkeypatch.setattr(
        "app.services.google_auth_service.verify_google_credential",
        reject_google_credential,
    )

    response = client.post(
        "/api/v1/auth/google",
        json={"credential": GOOGLE_CREDENTIAL},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == ("Unable to authenticate with Google.")


def test_google_login_requires_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_missing_configuration(
        credential: str,
    ) -> GoogleIdentity:
        raise GoogleAuthenticationConfigurationError

    monkeypatch.setattr(
        "app.services.google_auth_service.verify_google_credential",
        reject_missing_configuration,
    )

    response = client.post(
        "/api/v1/auth/google",
        json={"credential": GOOGLE_CREDENTIAL},
    )

    assert response.status_code == (status.HTTP_503_SERVICE_UNAVAILABLE)
    assert response.json()["detail"] == ("Google authentication is not configured.")


def test_google_login_requires_safe_account_linking(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_google_identity(monkeypatch)

    UserRepository(db_session).create(
        full_name="Existing Candidate",
        email="candidate@example.com",
        password_hash=hash_password("StrongPassword123!"),
        is_verified=True,
    )
    db_session.commit()

    response = client.post(
        "/api/v1/auth/google",
        json={"credential": GOOGLE_CREDENTIAL},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == (
        "An account already exists with this email. "
        "Log in using the existing method before linking Google."
    )


def test_google_login_rejects_inactive_user(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_google_identity(monkeypatch)

    first_response = client.post(
        "/api/v1/auth/google",
        json={"credential": GOOGLE_CREDENTIAL},
    )

    assert first_response.status_code == status.HTTP_200_OK

    user = UserRepository(db_session).get_by_email("candidate@example.com")

    assert user is not None

    user.is_active = False
    db_session.commit()

    second_response = client.post(
        "/api/v1/auth/google",
        json={"credential": GOOGLE_CREDENTIAL},
    )

    assert second_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert second_response.json()["detail"] == ("Unable to authenticate with Google.")
