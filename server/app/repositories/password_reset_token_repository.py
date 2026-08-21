from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_token_hash(
        self,
        token_hash: str,
        *,
        for_update: bool = False,
    ) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
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
    ) -> PasswordResetToken:
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.session.add(reset_token)

        return reset_token

    def mark_used(
        self,
        reset_token: PasswordResetToken,
        used_at: datetime,
    ) -> None:
        reset_token.used_at = used_at

    def invalidate_unused_for_user(
        self,
        user_id: UUID,
        used_at: datetime,
        *,
        exclude_token_id: UUID | None = None,
    ) -> int:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )

        if exclude_token_id is not None:
            statement = statement.where(PasswordResetToken.id != exclude_token_id)

        unused_tokens = list(self.session.scalars(statement))

        for reset_token in unused_tokens:
            reset_token.used_at = used_at

        return len(unused_tokens)
