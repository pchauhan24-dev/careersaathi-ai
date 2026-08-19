import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
)
from app.core.security import verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserLogin, UserRegister
from app.services.auth_service import (
    authenticate_user,
    register_user,
)


def create_registration_data() -> UserRegister:
    return UserRegister(
        full_name="Career Saathi",
        email="candidate@example.com",
        password="StrongPassword123!",
    )


def test_register_user(
    db_session: Session,
) -> None:
    registration_data = create_registration_data()
    user = register_user(db_session, registration_data)

    assert user.id is not None
    assert user.email == "candidate@example.com"
    assert user.is_verified is False
    assert user.password_hash != registration_data.password
    assert verify_password(
        registration_data.password,
        user.password_hash,
    )


def test_register_user_rejects_duplicate_email(
    db_session: Session,
) -> None:
    registration_data = create_registration_data()

    register_user(db_session, registration_data)

    with pytest.raises(EmailAlreadyRegisteredError):
        register_user(db_session, registration_data)


def test_authenticate_user(
    db_session: Session,
) -> None:
    user = register_user(
        db_session,
        create_registration_data(),
    )

    user.is_verified = True
    db_session.commit()
    db_session.refresh(user)

    authenticated_user = authenticate_user(
        db_session,
        UserLogin(
            email="candidate@example.com",
            password="StrongPassword123!",
        ),
    )

    assert authenticated_user.id == user.id
    assert authenticated_user.email == "candidate@example.com"
    assert authenticated_user.is_verified is True


def test_authenticate_user_rejects_unverified_email(
    db_session: Session,
) -> None:
    register_user(
        db_session,
        create_registration_data(),
    )

    with pytest.raises(EmailNotVerifiedError):
        authenticate_user(
            db_session,
            UserLogin(
                email="candidate@example.com",
                password="StrongPassword123!",
            ),
        )


def test_authenticate_user_rejects_wrong_password(
    db_session: Session,
) -> None:
    register_user(
        db_session,
        create_registration_data(),
    )

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            db_session,
            UserLogin(
                email="candidate@example.com",
                password="WrongPassword123!",
            ),
        )


def test_authenticate_user_rejects_unknown_email(
    db_session: Session,
) -> None:
    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            db_session,
            UserLogin(
                email="unknown@example.com",
                password="StrongPassword123!",
            ),
        )


def test_password_login_rejects_social_only_account(
    db_session: Session,
) -> None:
    UserRepository(db_session).create(
        full_name="Social Candidate",
        email="social@example.com",
        password_hash=None,
        is_verified=True,
    )
    db_session.commit()

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            db_session,
            UserLogin(
                email="social@example.com",
                password="AnyPassword123!",
            ),
        )
