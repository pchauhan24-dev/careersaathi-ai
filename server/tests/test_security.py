from datetime import timedelta

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    plain_password = "StrongPassword123!"
    hashed_password = hash_password(plain_password)

    assert hashed_password != plain_password
    assert verify_password(plain_password, hashed_password) is True
    assert verify_password("WrongPassword123!", hashed_password) is False


def test_access_token_contains_subject() -> None:
    token = create_access_token("test-user-id")
    payload = decode_access_token(token)

    assert payload["sub"] == "test-user-id"
    assert payload["type"] == "access"


def test_expired_access_token_is_rejected() -> None:
    token = create_access_token(
        "test-user-id",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
