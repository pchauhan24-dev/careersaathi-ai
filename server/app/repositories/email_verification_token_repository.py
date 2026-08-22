from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email_verification_token import (
    EmailVerificationToken,
)


class EmailVerificationTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_token_hash(
        self,
        token_hash: str,
        *,
        for_update: bool = False,
    ) -> EmailVerificationToken | None:
        statement = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )

        if for_update:
            statement = statement.with_for_update()

        return self.session.scalar(statement)

    def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> EmailVerificationToken:
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.session.add(verification_token)

        return verification_token

    def mark_used(
        self,
        verification_token: EmailVerificationToken,
        used_at: datetime,
    ) -> None:
        verification_token.used_at = used_at

    def invalidate_unused_for_user(
        self,
        user_id: UUID,
        used_at: datetime,
        *,
        exclude_token_id: UUID | None = None,
    ) -> int:
        statement = select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None),
        )

        if exclude_token_id is not None:
            statement = statement.where(EmailVerificationToken.id != exclude_token_id)

        unused_tokens = list(self.session.scalars(statement))

        for verification_token in unused_tokens:
            verification_token.used_at = used_at

        return len(unused_tokens)
