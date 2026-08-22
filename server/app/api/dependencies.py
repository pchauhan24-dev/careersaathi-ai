from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    scheme_name="BearerAuth",
    auto_error=False,
)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)

        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Invalid token type.")

        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise jwt.InvalidTokenError("Invalid token subject.")

        user_id = UUID(subject)
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise authentication_error() from exc

    repository = UserRepository(session)
    user = repository.get_by_id(user_id)

    if user is None or not user.is_active:
        raise authentication_error()

    return user
