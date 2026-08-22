import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidCredentialsError,
    SocialAccountLinkingRequiredError,
)
from app.core.security import hash_password
from app.models.social_account import GOOGLE_PROVIDER
from app.repositories.social_account_repository import (
    SocialAccountRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.google_auth_service import (
    authenticate_google_user,
)
from app.services.google_identity_service import GoogleIdentity


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


def test_authenticate_google_user_creates_account(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_google_identity(monkeypatch)

    user = authenticate_google_user(
        db_session,
        "x" * 100,
    )

    social_account = SocialAccountRepository(db_session).get_by_provider_subject(
        GOOGLE_PROVIDER,
        "google-user-123",
    )

    assert user.id is not None
    assert user.full_name == "Career Saathi"
    assert user.email == "candidate@example.com"
    assert user.password_hash is None
    assert user.is_verified is True
    assert user.is_active is True

    assert social_account is not None
    assert social_account.user_id == user.id
    assert social_account.provider == GOOGLE_PROVIDER
    assert social_account.provider_subject == "google-user-123"
    assert social_account.provider_email == "candidate@example.com"


def test_authenticate_google_user_returns_existing_social_user(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_google_identity(monkeypatch)

    first_user = authenticate_google_user(
        db_session,
        "x" * 100,
    )
    second_user = authenticate_google_user(
        db_session,
        "y" * 100,
    )

    social_accounts = SocialAccountRepository(db_session).list_by_user(first_user.id)

    assert second_user.id == first_user.id
    assert len(social_accounts) == 1


def test_google_authentication_requires_safe_account_linking(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_google_identity(monkeypatch)

    existing_user = UserRepository(db_session).create(
        full_name="Existing Candidate",
        email="candidate@example.com",
        password_hash=hash_password("StrongPassword123!"),
        is_verified=True,
    )

    db_session.commit()
    db_session.refresh(existing_user)

    with pytest.raises(SocialAccountLinkingRequiredError):
        authenticate_google_user(
            db_session,
            "x" * 100,
        )

    social_accounts = SocialAccountRepository(db_session).list_by_user(existing_user.id)

    assert social_accounts == []


def test_google_authentication_rejects_inactive_user(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_google_identity(monkeypatch)

    user = authenticate_google_user(
        db_session,
        "x" * 100,
    )

    user.is_active = False
    db_session.commit()

    with pytest.raises(InvalidCredentialsError):
        authenticate_google_user(
            db_session,
            "y" * 100,
        )
