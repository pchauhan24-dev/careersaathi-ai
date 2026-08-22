from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    InvalidEmailVerificationTokenError,
)
from app.core.security import (
    generate_email_verification_token,
    hash_email_verification_token,
)
from app.models.email_verification_token import (
    EmailVerificationToken,
)
from app.models.user import User
from app.repositories.email_verification_token_repository import (
    EmailVerificationTokenRepository,
)
from app.repositories.user_repository import UserRepository

MAX_TOKEN_GENERATION_ATTEMPTS = 3


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def create_email_verification_token(
    session: Session,
    user_id: UUID,
    *,
    expires_at: datetime | None = None,
) -> tuple[EmailVerificationToken, str]:
    repository = EmailVerificationTokenRepository(session)
    current_time = datetime.now(UTC)

    token_expiration = expires_at or (
        current_time + timedelta(hours=settings.email_verification_token_expire_hours)
    )

    for _ in range(MAX_TOKEN_GENERATION_ATTEMPTS):
        repository.invalidate_unused_for_user(
            user_id,
            current_time,
        )

        raw_verification_token = generate_email_verification_token()

        verification_token = repository.create(
            user_id=user_id,
            token_hash=hash_email_verification_token(raw_verification_token),
            expires_at=token_expiration,
        )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            continue

        session.refresh(verification_token)

        return verification_token, raw_verification_token

    raise RuntimeError("Unable to create an email verification token.")


def verify_email_verification_token(
    session: Session,
    raw_verification_token: str,
) -> User:
    repository = EmailVerificationTokenRepository(session)
    current_time = datetime.now(UTC)

    verification_token = repository.get_by_token_hash(
        hash_email_verification_token(raw_verification_token),
        for_update=True,
    )

    if verification_token is None or verification_token.used_at is not None:
        raise InvalidEmailVerificationTokenError

    expires_at = normalize_datetime(verification_token.expires_at)

    if expires_at <= current_time:
        repository.mark_used(
            verification_token,
            current_time,
        )
        session.commit()

        raise InvalidEmailVerificationTokenError

    user = verification_token.user

    if not user.is_active:
        repository.mark_used(
            verification_token,
            current_time,
        )
        session.commit()

        raise InvalidEmailVerificationTokenError

    user.is_verified = True

    repository.mark_used(
        verification_token,
        current_time,
    )

    repository.invalidate_unused_for_user(
        user.id,
        current_time,
        exclude_token_id=verification_token.id,
    )

    session.commit()
    session.refresh(user)

    return user


def request_email_verification(
    session: Session,
    email: str,
) -> tuple[User, str] | None:
    user_repository = UserRepository(session)
    normalized_email = email.lower()

    user = user_repository.get_by_email(normalized_email)

    if user is None or not user.is_active or user.is_verified:
        return None

    _, raw_verification_token = create_email_verification_token(
        session,
        user.id,
    )

    return user, raw_verification_token
