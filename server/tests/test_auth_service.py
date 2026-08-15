import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyRegisteredError
from app.core.security import verify_password
from app.schemas.auth import UserRegister
from app.services.auth_service import register_user


def test_register_user(
    db_session: Session,
) -> None:
    registration_data = UserRegister(
        full_name="Career Saathi",
        email="candidate@example.com",
        password="StrongPassword123!",
    )

    user = register_user(db_session, registration_data)

    assert user.id is not None
    assert user.full_name == "Career Saathi"
    assert user.email == "candidate@example.com"
    assert user.password_hash != registration_data.password
    assert verify_password(
        registration_data.password,
        user.password_hash,
    )


def test_register_user_rejects_duplicate_email(
    db_session: Session,
) -> None:
    registration_data = UserRegister(
        full_name="Career Saathi",
        email="candidate@example.com",
        password="StrongPassword123!",
    )

    register_user(db_session, registration_data)

    with pytest.raises(EmailAlreadyRegisteredError):
        register_user(db_session, registration_data)
