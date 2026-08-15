from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserLogin, UserRegister

DUMMY_PASSWORD_HASH = hash_password("CareerSaathi-Dummy-Password-For-Timing-Protection")


def register_user(
    session: Session,
    registration_data: UserRegister,
) -> User:
    repository = UserRepository(session)
    normalized_email = str(registration_data.email).lower()

    existing_user = repository.get_by_email(normalized_email)

    if existing_user is not None:
        raise EmailAlreadyRegisteredError

    user = repository.create(
        full_name=registration_data.full_name,
        email=normalized_email,
        password_hash=hash_password(registration_data.password),
    )

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise EmailAlreadyRegisteredError from exc

    session.refresh(user)

    return user


def authenticate_user(
    session: Session,
    login_data: UserLogin,
) -> User:
    repository = UserRepository(session)
    normalized_email = str(login_data.email).lower()
    user = repository.get_by_email(normalized_email)

    if user is None:
        verify_password(
            login_data.password,
            DUMMY_PASSWORD_HASH,
        )
        raise InvalidCredentialsError

    password_is_valid = verify_password(
        login_data.password,
        user.password_hash,
    )

    if not password_is_valid or not user.is_active:
        raise InvalidCredentialsError

    return user
