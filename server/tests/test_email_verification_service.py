from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidEmailVerificationTokenError,
)
from app.core.security import (
    hash_email_verification_token,
)
from app.models.user import User
from app.repositories.email_verification_token_repository import (
    EmailVerificationTokenRepository,
)
from app.schemas.auth import UserRegister
from app.services.auth_service import register_user
from app.services.email_verification_service import (
    create_email_verification_token,
    verify_email_verification_token,
)


def create_test_user(
    db_session: Session,
    email: str = "candidate@example.com",
) -> User:
    return register_user(
        db_session,
        UserRegister(
            full_name="Career Saathi",
            email=email,
            password="StrongPassword123!",
        ),
    )


def test_create_email_verification_token(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    verification_token, raw_token = create_email_verification_token(
        db_session,
        user.id,
    )

    repository = EmailVerificationTokenRepository(db_session)

    stored_token = repository.get_by_token_hash(
        hash_email_verification_token(raw_token)
    )

    expires_at = verification_token.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    assert stored_token is not None
    assert stored_token.id == verification_token.id
    assert verification_token.token_hash != raw_token
    assert verification_token.used_at is None
    assert expires_at > datetime.now(UTC)


def test_new_token_invalidates_previous_token(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    first_token, first_raw_token = create_email_verification_token(
        db_session,
        user.id,
    )

    second_token, second_raw_token = create_email_verification_token(
        db_session,
        user.id,
    )

    db_session.refresh(first_token)

    assert first_raw_token != second_raw_token
    assert first_token.id != second_token.id
    assert first_token.used_at is not None
    assert second_token.used_at is None


def test_verify_email_verification_token(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    verification_token, raw_token = create_email_verification_token(
        db_session,
        user.id,
    )

    verified_user = verify_email_verification_token(
        db_session,
        raw_token,
    )

    db_session.refresh(verification_token)

    assert verified_user.id == user.id
    assert verified_user.is_verified is True
    assert verification_token.used_at is not None


def test_verification_token_cannot_be_reused(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    _, raw_token = create_email_verification_token(
        db_session,
        user.id,
    )

    verify_email_verification_token(
        db_session,
        raw_token,
    )

    with pytest.raises(InvalidEmailVerificationTokenError):
        verify_email_verification_token(
            db_session,
            raw_token,
        )


def test_expired_verification_token_is_rejected(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    verification_token, raw_token = create_email_verification_token(
        db_session,
        user.id,
        expires_at=(datetime.now(UTC) - timedelta(seconds=1)),
    )

    with pytest.raises(InvalidEmailVerificationTokenError):
        verify_email_verification_token(
            db_session,
            raw_token,
        )

    db_session.refresh(verification_token)
    db_session.refresh(user)

    assert verification_token.used_at is not None
    assert user.is_verified is False
