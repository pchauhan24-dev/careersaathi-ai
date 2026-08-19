from app.models.social_account import SocialAccount
from app.models.user import User


def test_social_account_model_schema() -> None:
    expected_columns = {
        "id",
        "user_id",
        "provider",
        "provider_subject",
        "provider_email",
        "created_at",
        "updated_at",
    }

    assert SocialAccount.__tablename__ == "social_accounts"
    assert set(SocialAccount.__table__.columns.keys()) == (expected_columns)
    assert SocialAccount.__table__.c.id.primary_key is True
    assert SocialAccount.__table__.c.user_id.nullable is False
    assert SocialAccount.__table__.c.provider.nullable is False
    assert SocialAccount.__table__.c.provider_subject.nullable is False
    assert SocialAccount.__table__.c.provider_email.nullable is True

    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key in SocialAccount.__table__.foreign_keys
    }

    assert foreign_keys == {"users.id"}

    constraint_names = {
        constraint.name
        for constraint in SocialAccount.__table__.constraints
        if constraint.name is not None
    }

    assert "ck_social_accounts_provider" in constraint_names
    assert "uq_social_accounts_provider_subject" in constraint_names
    assert "uq_social_accounts_user_provider" in constraint_names


def test_social_account_relationships() -> None:
    assert SocialAccount.user.property.back_populates == ("social_accounts")
    assert User.social_accounts.property.back_populates == "user"
