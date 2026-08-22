from app.models.user import User


def test_user_model_table_name() -> None:
    assert User.__tablename__ == "users"


def test_user_model_columns() -> None:
    expected_columns = {
        "id",
        "full_name",
        "email",
        "password_hash",
        "is_active",
        "is_verified",
        "created_at",
        "updated_at",
    }

    assert set(User.__table__.columns.keys()) == expected_columns
    assert User.__table__.c.id.primary_key is True
    assert User.__table__.c.email.unique is True
    assert User.__table__.c.password_hash.nullable is True
