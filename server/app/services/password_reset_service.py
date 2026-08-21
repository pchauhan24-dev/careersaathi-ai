from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import InvalidPasswordResetTokenError
from app.core.security import (
    generate_password_reset_token,
    hash_password,
    hash_password_reset_token,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.repositories.user_repository import UserRepository

MAX_TOKEN_GENERATION_ATTEMPTS = 3


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def create_password_reset_token(
    session: Session,
    user_id: UUID,
    *,
    expires_at: datetime | None = None,
) -> tuple[PasswordResetToken, str]:
    repository = PasswordResetTokenRepository(session)
    current_time = datetime.now(UTC)

    token_expiration = expires_at or (
        current_time + timedelta(minutes=settings.password_reset_token_expire_minutes)
    )

    for _ in range(MAX_TOKEN_GENERATION_ATTEMPTS):
        repository.invalidate_unused_for_user(
            user_id,
            current_time,
        )

        raw_reset_token = generate_password_reset_token()

        reset_token = repository.create(
            user_id=user_id,
            token_hash=hash_password_reset_token(raw_reset_token),
            expires_at=token_expiration,
        )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            continue

        session.refresh(reset_token)

        return reset_token, raw_reset_token

    raise RuntimeError("Unable to create a password reset token.")


def request_password_reset(
    session: Session,
    email: str,
) -> tuple[User, str] | None:
    user_repository = UserRepository(session)
    normalized_email = email.strip().lower()

    user = user_repository.get_by_email(normalized_email)

    if user is None or not user.is_active:
        return None

    _, raw_reset_token = create_password_reset_token(
        session,
        user.id,
    )

    return user, raw_reset_token


def reset_user_password(
    session: Session,
    raw_reset_token: str,
    new_password: str,
) -> User:
    reset_repository = PasswordResetTokenRepository(session)
    auth_session_repository = AuthSessionRepository(session)
    current_time = datetime.now(UTC)

    reset_token = reset_repository.get_by_token_hash(
        hash_password_reset_token(raw_reset_token),
        for_update=True,
    )

    if reset_token is None or reset_token.used_at is not None:
        raise InvalidPasswordResetTokenError

    expires_at = normalize_datetime(reset_token.expires_at)

    if expires_at <= current_time:
        reset_repository.mark_used(
            reset_token,
            current_time,
        )
        session.commit()

        raise InvalidPasswordResetTokenError

    user = reset_token.user

    if not user.is_active:
        reset_repository.mark_used(
            reset_token,
            current_time,
        )
        session.commit()

        raise InvalidPasswordResetTokenError

    user.password_hash = hash_password(new_password)
    user.is_verified = True

    reset_repository.mark_used(
        reset_token,
        current_time,
    )

    reset_repository.invalidate_unused_for_user(
        user.id,
        current_time,
        exclude_token_id=reset_token.id,
    )

    auth_session_repository.revoke_all_for_user(
        user.id,
        current_time,
    )

    session.commit()
    session.refresh(user)

    return user
