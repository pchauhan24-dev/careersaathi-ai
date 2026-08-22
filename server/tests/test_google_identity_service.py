import pytest

from app.core.config import settings
from app.core.exceptions import (
    GoogleAuthenticationConfigurationError,
    InvalidGoogleCredentialError,
)
from app.services.google_identity_service import (
    verify_google_credential,
)


def test_verify_google_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_verify_token(
        credential,
        request,
        audience,
    ):
        return {
            "iss": "https://accounts.google.com",
            "sub": "google-user-123",
            "email": "Candidate@Example.com",
            "email_verified": True,
            "name": "  Career   Saathi  ",
        }

    monkeypatch.setattr(
        settings,
        "google_client_id",
        "test-client-id.apps.googleusercontent.com",
    )
    monkeypatch.setattr(
        "app.services.google_identity_service.google_id_token.verify_oauth2_token",
        fake_verify_token,
    )

    identity = verify_google_credential("x" * 100)

    assert identity.subject == "google-user-123"
    assert identity.email == "candidate@example.com"
    assert identity.full_name == "Career Saathi"


def test_verify_google_credential_rejects_invalid_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_verify_token(
        credential,
        request,
        audience,
    ):
        raise ValueError("Invalid token")

    monkeypatch.setattr(
        settings,
        "google_client_id",
        "test-client-id.apps.googleusercontent.com",
    )
    monkeypatch.setattr(
        "app.services.google_identity_service.google_id_token.verify_oauth2_token",
        fake_verify_token,
    )

    with pytest.raises(InvalidGoogleCredentialError):
        verify_google_credential("x" * 100)


def test_verify_google_credential_rejects_unverified_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_verify_token(
        credential,
        request,
        audience,
    ):
        return {
            "iss": "accounts.google.com",
            "sub": "google-user-123",
            "email": "candidate@example.com",
            "email_verified": False,
            "name": "Career Saathi",
        }

    monkeypatch.setattr(
        settings,
        "google_client_id",
        "test-client-id.apps.googleusercontent.com",
    )
    monkeypatch.setattr(
        "app.services.google_identity_service.google_id_token.verify_oauth2_token",
        fake_verify_token,
    )

    with pytest.raises(InvalidGoogleCredentialError):
        verify_google_credential("x" * 100)


def test_verify_google_credential_requires_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "google_client_id",
        None,
    )

    with pytest.raises(GoogleAuthenticationConfigurationError):
        verify_google_credential("x" * 100)
