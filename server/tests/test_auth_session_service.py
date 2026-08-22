from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidRefreshTokenError
from app.core.security import hash_refresh_token
from app.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from app.schemas.auth import UserRegister
from app.services.auth_service import register_user
from app.services.auth_session_service import (
    create_refresh_session,
    rotate_refresh_session,
)


def create_test_user(
    db_session: Session,
    email: str = "candidate@example.com",
):
    return register_user(
        db_session,
        UserRegister(
            full_name="Career Saathi",
            email=email,
            password="StrongPassword123!",
        ),
    )


def test_create_refresh_session(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    auth_session, raw_refresh_token = create_refresh_session(
        db_session,
        user.id,
    )

    repository = AuthSessionRepository(db_session)
    stored_session = repository.get_by_refresh_token_hash(
        hash_refresh_token(raw_refresh_token)
    )

    expires_at = auth_session.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    assert stored_session is not None
    assert stored_session.id == auth_session.id
    assert auth_session.refresh_token_hash != raw_refresh_token
    assert expires_at > datetime.now(UTC)


def test_create_refresh_sessions_are_unique(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    first_session, first_token = create_refresh_session(
        db_session,
        user.id,
    )
    second_session, second_token = create_refresh_session(
        db_session,
        user.id,
    )

    assert first_session.id != second_session.id
    assert first_session.family_id != second_session.family_id
    assert first_token != second_token


def test_rotate_refresh_session(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    old_session, old_token = create_refresh_session(
        db_session,
        user.id,
    )

    rotated_user, new_session, new_token = rotate_refresh_session(
        db_session,
        old_token,
    )

    db_session.refresh(old_session)

    assert rotated_user.id == user.id
    assert new_session.id != old_session.id
    assert new_session.family_id == old_session.family_id
    assert new_token != old_token
    assert old_session.revoked_at is not None
    assert old_session.replaced_by_session_id == new_session.id
    assert new_session.revoked_at is None


def test_rotate_rejects_expired_refresh_token(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    expired_session, expired_token = create_refresh_session(
        db_session,
        user.id,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_session(
            db_session,
            expired_token,
        )

    db_session.refresh(expired_session)

    assert expired_session.revoked_at is not None


def test_refresh_token_reuse_revokes_family(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    _, old_token = create_refresh_session(
        db_session,
        user.id,
    )

    _, current_session, _ = rotate_refresh_session(
        db_session,
        old_token,
    )

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_session(
            db_session,
            old_token,
        )

    db_session.refresh(current_session)

    assert current_session.revoked_at is not None
