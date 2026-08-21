import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidCredentialsError,
    SocialAccountLinkingRequiredError,
)
from app.models.social_account import GITHUB_PROVIDER
from app.repositories.social_account_repository import (
    SocialAccountRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.github_auth_service import (
    authenticate_github_user,
)
from app.services.github_identity_service import GitHubIdentity


def configure_github_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    subject: str = "123456",
    email: str = "candidate@example.com",
    full_name: str = "Career Saathi",
) -> None:
    def fake_exchange(
        authorization_code: str,
        code_verifier: str,
    ) -> str:
        assert authorization_code == "github-authorization-code"
        assert code_verifier == "v" * 64

        return "temporary-github-access-token"

    def fake_retrieve(
        access_token: str,
    ) -> GitHubIdentity:
        assert access_token == "temporary-github-access-token"

        return GitHubIdentity(
            subject=subject,
            email=email,
            full_name=full_name,
        )

    monkeypatch.setattr(
        "app.services.github_auth_service.exchange_github_authorization_code",
        fake_exchange,
    )
    monkeypatch.setattr(
        "app.services.github_auth_service.retrieve_github_identity",
        fake_retrieve,
    )


def authenticate_test_github_user(
    db_session: Session,
):
    return authenticate_github_user(
        db_session,
        "github-authorization-code",
        "v" * 64,
    )


def test_authenticate_new_github_user(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_identity(monkeypatch)

    user = authenticate_test_github_user(db_session)

    social_account = SocialAccountRepository(db_session).get_by_provider_subject(
        GITHUB_PROVIDER,
        "123456",
    )

    assert user.id is not None
    assert user.full_name == "Career Saathi"
    assert user.email == "candidate@example.com"
    assert user.password_hash is None
    assert user.is_active is True
    assert user.is_verified is True

    assert social_account is not None
    assert social_account.user_id == user.id
    assert social_account.provider == GITHUB_PROVIDER
    assert social_account.provider_email == "candidate@example.com"


def test_authenticate_returning_github_user(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_identity(monkeypatch)

    first_user = authenticate_test_github_user(db_session)

    configure_github_identity(
        monkeypatch,
        email="updated@example.com",
    )

    returning_user = authenticate_test_github_user(db_session)

    social_account = SocialAccountRepository(db_session).get_by_provider_subject(
        GITHUB_PROVIDER,
        "123456",
    )

    assert returning_user.id == first_user.id
    assert returning_user.email == "candidate@example.com"
    assert social_account is not None
    assert social_account.provider_email == "updated@example.com"


def test_github_authentication_requires_safe_account_linking(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_identity(monkeypatch)

    existing_user = UserRepository(db_session).create(
        full_name="Existing Candidate",
        email="candidate@example.com",
        password_hash="existing-password-hash",
        is_verified=True,
    )

    db_session.commit()
    db_session.refresh(existing_user)

    with pytest.raises(
        SocialAccountLinkingRequiredError,
        match=("Log in using the existing method before linking GitHub."),
    ):
        authenticate_test_github_user(db_session)

    social_account = SocialAccountRepository(db_session).get_by_provider_subject(
        GITHUB_PROVIDER,
        "123456",
    )

    assert social_account is None


def test_github_authentication_rejects_inactive_user(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_identity(monkeypatch)

    user = authenticate_test_github_user(db_session)

    user.is_active = False
    db_session.commit()

    with pytest.raises(InvalidCredentialsError):
        authenticate_test_github_user(db_session)
