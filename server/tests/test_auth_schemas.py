import pytest
from pydantic import ValidationError

from app.schemas.auth import UserRegister


def test_registration_data_is_normalized() -> None:
    registration_data = UserRegister(
        full_name="  Career   Saathi  ",
        email="TEST@EXAMPLE.COM",
        password="StrongPassword123!",
    )

    assert registration_data.full_name == "Career Saathi"
    assert registration_data.email == "test@example.com"


def test_registration_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserRegister(
            full_name="Career Saathi",
            email="invalid-email",
            password="StrongPassword123!",
        )


def test_registration_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserRegister(
            full_name="Career Saathi",
            email="test@example.com",
            password="short",
        )
