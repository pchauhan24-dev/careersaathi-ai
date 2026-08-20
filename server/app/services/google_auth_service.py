from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidCredentialsError,
    SocialAccountLinkingRequiredError,
    SocialAuthenticationConflictError,
)
from app.models.social_account import GOOGLE_PROVIDER
from app.models.user import User
from app.repositories.social_account_repository import (
    SocialAccountRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.google_identity_service import (
    GoogleIdentity,
    verify_google_credential,
)


def get_returning_google_user(
    social_account_repository: SocialAccountRepository,
    identity: GoogleIdentity,
) -> User | None:
    social_account = social_account_repository.get_by_provider_subject(
        GOOGLE_PROVIDER,
        identity.subject,
    )

    if social_account is None:
        return None

    user = social_account.user

    if not user.is_active:
        raise InvalidCredentialsError

    if social_account.provider_email != identity.email:
        social_account.provider_email = identity.email
        social_account_repository.session.commit()

    return user


def authenticate_google_user(
    session: Session,
    credential: str,
) -> User:
    identity = verify_google_credential(credential)

    user_repository = UserRepository(session)
    social_account_repository = SocialAccountRepository(session)

    returning_user = get_returning_google_user(
        social_account_repository,
        identity,
    )

    if returning_user is not None:
        return returning_user

    existing_user = user_repository.get_by_email(identity.email)

    if existing_user is not None:
        raise SocialAccountLinkingRequiredError

    user = user_repository.create(
        full_name=identity.full_name,
        email=identity.email,
        password_hash=None,
        is_verified=True,
    )

    try:
        session.flush()

        social_account_repository.create(
            user_id=user.id,
            provider=GOOGLE_PROVIDER,
            provider_subject=identity.subject,
            provider_email=identity.email,
        )

        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise SocialAuthenticationConflictError from exc

    session.refresh(user)

    return user
