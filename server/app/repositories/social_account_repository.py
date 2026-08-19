from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.social_account import (
    SUPPORTED_SOCIAL_PROVIDERS,
    SocialAccount,
)


def normalize_social_provider(provider: str) -> str:
    normalized_provider = provider.strip().lower()

    if normalized_provider not in SUPPORTED_SOCIAL_PROVIDERS:
        raise ValueError("Unsupported social authentication provider.")

    return normalized_provider


class SocialAccountRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_provider_subject(
        self,
        provider: str,
        provider_subject: str,
    ) -> SocialAccount | None:
        normalized_provider = normalize_social_provider(provider)

        statement = select(SocialAccount).where(
            SocialAccount.provider == normalized_provider,
            SocialAccount.provider_subject == provider_subject,
        )

        return self.session.scalar(statement)

    def get_by_user_and_provider(
        self,
        user_id: UUID,
        provider: str,
    ) -> SocialAccount | None:
        normalized_provider = normalize_social_provider(provider)

        statement = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.provider == normalized_provider,
        )

        return self.session.scalar(statement)

    def list_by_user(
        self,
        user_id: UUID,
    ) -> list[SocialAccount]:
        statement = select(SocialAccount).where(SocialAccount.user_id == user_id)

        return list(self.session.scalars(statement))

    def create(
        self,
        *,
        user_id: UUID,
        provider: str,
        provider_subject: str,
        provider_email: str | None = None,
    ) -> SocialAccount:
        normalized_provider = normalize_social_provider(provider)
        normalized_subject = provider_subject.strip()

        if not normalized_subject:
            raise ValueError("Provider subject cannot be empty.")

        normalized_email = (
            provider_email.strip().lower() if provider_email is not None else None
        )

        social_account = SocialAccount(
            user_id=user_id,
            provider=normalized_provider,
            provider_subject=normalized_subject,
            provider_email=normalized_email,
        )

        self.session.add(social_account)

        return social_account
