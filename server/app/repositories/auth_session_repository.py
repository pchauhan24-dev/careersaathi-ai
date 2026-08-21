from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth_session import AuthSession


class AuthSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_refresh_token_hash(
        self,
        refresh_token_hash: str,
    ) -> AuthSession | None:
        statement = select(AuthSession).where(
            AuthSession.refresh_token_hash == refresh_token_hash
        )

        return self.session.scalar(statement)

    def create(
        self,
        *,
        user_id: UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        family_id: UUID | None = None,
    ) -> AuthSession:
        auth_session = AuthSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )

        if family_id is not None:
            auth_session.family_id = family_id

        self.session.add(auth_session)

        return auth_session

    def revoke(
        self,
        auth_session: AuthSession,
        revoked_at: datetime,
        *,
        replaced_by_session_id: UUID | None = None,
    ) -> None:
        auth_session.revoked_at = revoked_at
        auth_session.replaced_by_session_id = replaced_by_session_id

    def revoke_family(
        self,
        family_id: UUID,
        revoked_at: datetime,
    ) -> int:
        statement = select(AuthSession).where(
            AuthSession.family_id == family_id,
            AuthSession.revoked_at.is_(None),
        )

        active_sessions = list(self.session.scalars(statement))

        for auth_session in active_sessions:
            auth_session.revoked_at = revoked_at

        return len(active_sessions)

    def revoke_all_for_user(
        self,
        user_id: UUID,
        revoked_at: datetime,
    ) -> int:
        statement = select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
        )

        active_sessions = list(self.session.scalars(statement))

        for auth_session in active_sessions:
            auth_session.revoked_at = revoked_at

        return len(active_sessions)
