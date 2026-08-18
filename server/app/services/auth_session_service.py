from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import InvalidRefreshTokenError
from app.core.security import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.auth_session import AuthSession
from app.models.user import User
from app.repositories.auth_session_repository import (
    AuthSessionRepository,
)

MAX_TOKEN_GENERATION_ATTEMPTS = 3


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def create_refresh_session(
    session: Session,
    user_id: UUID,
    *,
    family_id: UUID | None = None,
    expires_at: datetime | None = None,
) -> tuple[AuthSession, str]:
    repository = AuthSessionRepository(session)

    session_expiration = expires_at or (
        datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    )

    for _ in range(MAX_TOKEN_GENERATION_ATTEMPTS):
        raw_refresh_token = generate_refresh_token()

        auth_session = repository.create(
            user_id=user_id,
            refresh_token_hash=hash_refresh_token(raw_refresh_token),
            expires_at=session_expiration,
            family_id=family_id,
        )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            continue

        session.refresh(auth_session)

        return auth_session, raw_refresh_token

    raise RuntimeError("Unable to create an authentication session.")


def rotate_refresh_session(
    session: Session,
    raw_refresh_token: str,
) -> tuple[User, AuthSession, str]:
    repository = AuthSessionRepository(session)
    current_time = datetime.now(UTC)

    current_session = repository.get_by_refresh_token_hash(
        hash_refresh_token(raw_refresh_token)
    )

    if current_session is None:
        raise InvalidRefreshTokenError

    if current_session.revoked_at is not None:
        repository.revoke_family(
            current_session.family_id,
            current_time,
        )
        session.commit()

        raise InvalidRefreshTokenError

    expires_at = normalize_datetime(current_session.expires_at)

    if expires_at <= current_time:
        repository.revoke(
            current_session,
            current_time,
        )
        session.commit()

        raise InvalidRefreshTokenError

    user = current_session.user

    if not user.is_active:
        repository.revoke_family(
            current_session.family_id,
            current_time,
        )
        session.commit()

        raise InvalidRefreshTokenError

    new_raw_refresh_token = generate_refresh_token()

    new_session = repository.create(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(new_raw_refresh_token),
        expires_at=current_session.expires_at,
        family_id=current_session.family_id,
    )

    try:
        session.flush()

        repository.revoke(
            current_session,
            current_time,
            replaced_by_session_id=new_session.id,
        )

        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise RuntimeError("Unable to rotate the authentication session.") from exc

    session.refresh(new_session)

    return user, new_session, new_raw_refresh_token


def revoke_refresh_session(
    session: Session,
    raw_refresh_token: str,
) -> None:
    repository = AuthSessionRepository(session)

    auth_session = repository.get_by_refresh_token_hash(
        hash_refresh_token(raw_refresh_token)
    )

    if auth_session is None or auth_session.revoked_at is not None:
        return

    repository.revoke(
        auth_session,
        datetime.now(UTC),
    )
    session.commit()
