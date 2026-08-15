import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.core.security import verify_password
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
    register_user(
        db_session,
        create_registration_data(),
    )

    user = authenticate_user(
        db_session,
        UserLogin(
            email="candidate@example.com",
            password="StrongPassword123!",
        ),
    )

    assert user.email == "candidate@example.com"


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
