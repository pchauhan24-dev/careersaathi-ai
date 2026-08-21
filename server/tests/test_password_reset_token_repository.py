from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import (
    generate_password_reset_token,
    hash_password_reset_token,
)
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.schemas.auth import UserRegister
from app.services.auth_service import register_user


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


def test_create_and_find_password_reset_token(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    repository = PasswordResetTokenRepository(db_session)

    raw_token = generate_password_reset_token()
    token_hash = hash_password_reset_token(raw_token)

    reset_token = repository.create(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )

    db_session.commit()
    db_session.refresh(reset_token)

    stored_token = repository.get_by_token_hash(token_hash)

    assert stored_token is not None
    assert stored_token.id == reset_token.id
    assert stored_token.user_id == user.id
    assert stored_token.token_hash == token_hash
    assert stored_token.token_hash != raw_token
    assert stored_token.used_at is None


def test_invalidate_unused_password_reset_tokens(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    repository = PasswordResetTokenRepository(db_session)

    first_token = repository.create(
        user_id=user.id,
        token_hash=hash_password_reset_token(generate_password_reset_token()),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )

    second_token = repository.create(
        user_id=user.id,
        token_hash=hash_password_reset_token(generate_password_reset_token()),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )

    db_session.commit()
    db_session.refresh(first_token)
    db_session.refresh(second_token)

    invalidated_at = datetime.now(UTC)

    invalidated_count = repository.invalidate_unused_for_user(
        user.id,
        invalidated_at,
        exclude_token_id=first_token.id,
    )

    db_session.commit()
    db_session.refresh(first_token)
    db_session.refresh(second_token)

    assert invalidated_count == 1
    assert first_token.used_at is None
    assert second_token.used_at is not None
