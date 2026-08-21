import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    issued_at = datetime.now(UTC)

    token_lifetime = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": issued_at,
        "exp": issued_at + token_lifetime,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={
            "require": [
                "sub",
                "type",
                "iat",
                "exp",
            ]
        },
    )


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(
        refresh_token.encode("utf-8"),
    ).hexdigest()


def generate_email_verification_token() -> str:
    return secrets.token_urlsafe(32)


def hash_email_verification_token(
    verification_token: str,
) -> str:
    return hashlib.sha256(
        verification_token.encode("utf-8"),
    ).hexdigest()


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password_reset_token(
    reset_token: str,
) -> str:
    return hashlib.sha256(
        reset_token.encode("utf-8"),
    ).hexdigest()
