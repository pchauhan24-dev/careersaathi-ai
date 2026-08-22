import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.social_account_repository import (
    SocialAccountRepository,
)
from app.repositories.user_repository import UserRepository


def create_social_user(
    db_session: Session,
) -> User:
    user = UserRepository(db_session).create(
        full_name="Career Saathi",
        email="candidate@example.com",
        password_hash=None,
        is_verified=True,
    )

    db_session.commit()
    db_session.refresh(user)

    return user


def test_create_and_find_social_account(
    db_session: Session,
) -> None:
    user = create_social_user(db_session)
    repository = SocialAccountRepository(db_session)

    social_account = repository.create(
        user_id=user.id,
        provider="GitHub",
        provider_subject="github-user-123",
        provider_email="Candidate@Example.com",
    )

    db_session.commit()
    db_session.refresh(social_account)

    stored_by_subject = repository.get_by_provider_subject(
        "github",
        "github-user-123",
    )
    stored_by_user = repository.get_by_user_and_provider(
        user.id,
        "GITHUB",
    )

    assert stored_by_subject is not None
    assert stored_by_user is not None
    assert stored_by_subject.id == social_account.id
    assert stored_by_user.id == social_account.id
    assert social_account.user_id == user.id
    assert social_account.provider == "github"
    assert social_account.provider_email == "candidate@example.com"
    assert social_account.user.id == user.id


def test_user_can_connect_supported_social_providers(
    db_session: Session,
) -> None:
    user = create_social_user(db_session)
    repository = SocialAccountRepository(db_session)

    repository.create(
        user_id=user.id,
        provider="google",
        provider_subject="google-user-123",
        provider_email=user.email,
    )
    repository.create(
        user_id=user.id,
        provider="github",
        provider_subject="github-user-456",
        provider_email=user.email,
    )
    repository.create(
        user_id=user.id,
        provider="linkedin",
        provider_subject="linkedin-user-789",
        provider_email=user.email,
    )

    db_session.commit()

    social_accounts = repository.list_by_user(user.id)

    assert len(social_accounts) == 3
    assert {social_account.provider for social_account in social_accounts} == {
        "google",
        "github",
        "linkedin",
    }


def test_repository_rejects_unsupported_provider(
    db_session: Session,
) -> None:
    user = create_social_user(db_session)
    repository = SocialAccountRepository(db_session)

    with pytest.raises(
        ValueError,
        match="Unsupported social authentication provider.",
    ):
        repository.create(
            user_id=user.id,
            provider="facebook",
            provider_subject="facebook-user-123",
        )
