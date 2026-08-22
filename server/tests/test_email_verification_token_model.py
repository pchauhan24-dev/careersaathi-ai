from app.models.email_verification_token import (
    EmailVerificationToken,
)


def test_email_verification_token_columns() -> None:
    table = EmailVerificationToken.__table__

    expected_columns = {
        "id",
        "user_id",
        "token_hash",
        "expires_at",
        "used_at",
        "created_at",
        "updated_at",
    }

    assert expected_columns.issubset(table.columns.keys())
    assert table.c.token_hash.unique is True
    assert table.c.user_id.nullable is False
    assert table.c.expires_at.nullable is False
    assert table.c.used_at.nullable is True


def test_email_verification_token_user_foreign_key() -> None:
    table = EmailVerificationToken.__table__
    foreign_key = next(iter(table.c.user_id.foreign_keys))

    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"
    assert (
        EmailVerificationToken.user.property.back_populates
        == "email_verification_tokens"
    )
