from app.models.password_reset_token import PasswordResetToken
from app.models.user import User


def test_password_reset_token_model_schema() -> None:
    expected_columns = {
        "id",
        "user_id",
        "token_hash",
        "expires_at",
        "used_at",
        "created_at",
        "updated_at",
    }

    assert PasswordResetToken.__tablename__ == "password_reset_tokens"
    assert set(PasswordResetToken.__table__.columns.keys()) == expected_columns
    assert PasswordResetToken.__table__.c.id.primary_key is True
    assert PasswordResetToken.__table__.c.user_id.nullable is False
    assert PasswordResetToken.__table__.c.token_hash.nullable is False
    assert PasswordResetToken.__table__.c.token_hash.unique is True
    assert PasswordResetToken.__table__.c.expires_at.nullable is False
    assert PasswordResetToken.__table__.c.used_at.nullable is True

    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key in PasswordResetToken.__table__.foreign_keys
    }

    assert foreign_keys == {"users.id"}


def test_password_reset_token_relationships() -> None:
    assert PasswordResetToken.user.property.back_populates == ("password_reset_tokens")
    assert User.password_reset_tokens.property.back_populates == "user"
