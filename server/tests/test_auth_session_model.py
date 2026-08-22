from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.auth_session import AuthSession
from app.schemas.auth import UserRegister
from app.services.auth_service import register_user


def test_auth_session_model_columns() -> None:
    expected_columns = {
        "id",
        "user_id",
        "family_id",
        "refresh_token_hash",
        "expires_at",
        "revoked_at",
        "replaced_by_session_id",
        "created_at",
        "updated_at",
    }

    assert set(AuthSession.__table__.columns.keys()) == expected_columns

    user_foreign_key = next(iter(AuthSession.__table__.c.user_id.foreign_keys))

    assert user_foreign_key.target_fullname == "users.id"


def test_auth_session_stores_only_refresh_token_hash(
    db_session: Session,
) -> None:
    user = register_user(
        db_session,
        UserRegister(
            full_name="Career Saathi",
            email="candidate@example.com",
            password="StrongPassword123!",
        ),
    )

    raw_refresh_token = generate_refresh_token()
    refresh_token_hash = hash_refresh_token(raw_refresh_token)

    auth_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=refresh_token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    db_session.add(auth_session)
    db_session.commit()
    db_session.refresh(auth_session)

    assert auth_session.id is not None
    assert auth_session.family_id is not None
    assert auth_session.refresh_token_hash == refresh_token_hash
    assert auth_session.refresh_token_hash != raw_refresh_token
    assert auth_session.user.id == user.id
