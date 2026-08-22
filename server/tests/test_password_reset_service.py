from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidPasswordResetTokenError
from app.core.security import (
    hash_password_reset_token,
    verify_password,
)
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.schemas.auth import UserRegister
from app.services.auth_service import register_user
from app.services.auth_session_service import create_refresh_session
from app.services.password_reset_service import (
    create_password_reset_token,
    request_password_reset,
    reset_user_password,
)


def create_test_user(
    db_session: Session,
):
    return register_user(
        db_session,
        UserRegister(
            full_name="Career Saathi",
            email="candidate@example.com",
            password="StrongPassword123!",
        ),
    )


def test_create_password_reset_token_invalidates_old_token(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    first_token, first_raw_token = create_password_reset_token(
        db_session,
        user.id,
    )

    second_token, second_raw_token = create_password_reset_token(
        db_session,
        user.id,
    )

    db_session.refresh(first_token)
    db_session.refresh(second_token)

    assert first_raw_token != second_raw_token
    assert first_token.used_at is not None
    assert second_token.used_at is None
    assert second_token.token_hash != second_raw_token


def test_request_password_reset_uses_generic_missing_user_result(
    db_session: Session,
) -> None:
    result = request_password_reset(
        db_session,
        "unknown@example.com",
    )

    assert result is None


def test_reset_user_password(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    first_auth_session, _ = create_refresh_session(
        db_session,
        user.id,
    )
    second_auth_session, _ = create_refresh_session(
        db_session,
        user.id,
    )

    reset_token, raw_reset_token = create_password_reset_token(
        db_session,
        user.id,
    )

    updated_user = reset_user_password(
        db_session,
        raw_reset_token,
        "NewStrongPassword456!",
    )

    db_session.refresh(reset_token)
    db_session.refresh(first_auth_session)
    db_session.refresh(second_auth_session)

    assert updated_user.password_hash is not None
    assert verify_password(
        "NewStrongPassword456!",
        updated_user.password_hash,
    )
    assert updated_user.is_verified is True
    assert reset_token.used_at is not None
    assert first_auth_session.revoked_at is not None
    assert second_auth_session.revoked_at is not None


def test_reset_user_password_rejects_reused_token(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    _, raw_reset_token = create_password_reset_token(
        db_session,
        user.id,
    )

    reset_user_password(
        db_session,
        raw_reset_token,
        "NewStrongPassword456!",
    )

    with pytest.raises(InvalidPasswordResetTokenError):
        reset_user_password(
            db_session,
            raw_reset_token,
            "AnotherStrongPassword789!",
        )


def test_reset_user_password_rejects_expired_token(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    reset_token, raw_reset_token = create_password_reset_token(
        db_session,
        user.id,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    with pytest.raises(InvalidPasswordResetTokenError):
        reset_user_password(
            db_session,
            raw_reset_token,
            "NewStrongPassword456!",
        )

    db_session.refresh(reset_token)

    assert reset_token.used_at is not None


def test_password_reset_token_is_stored_as_hash(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    _, raw_reset_token = create_password_reset_token(
        db_session,
        user.id,
    )

    repository = PasswordResetTokenRepository(db_session)

    stored_token = repository.get_by_token_hash(
        hash_password_reset_token(raw_reset_token)
    )

    assert stored_token is not None
    assert stored_token.token_hash != raw_reset_token
