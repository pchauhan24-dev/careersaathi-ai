from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User

GOOGLE_PROVIDER = "google"
LINKEDIN_PROVIDER = "linkedin"

SUPPORTED_SOCIAL_PROVIDERS = frozenset(
    {
        GOOGLE_PROVIDER,
        LINKEDIN_PROVIDER,
    }
)


class SocialAccount(TimestampMixin, Base):
    __tablename__ = "social_accounts"

    __table_args__ = (
        CheckConstraint(
            "provider IN ('google', 'linkedin')",
            name="ck_social_accounts_provider",
        ),
        UniqueConstraint(
            "provider",
            "provider_subject",
            name="uq_social_accounts_provider_subject",
        ),
        UniqueConstraint(
            "user_id",
            "provider",
            name="uq_social_accounts_user_provider",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    provider_subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    provider_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="social_accounts",
    )
