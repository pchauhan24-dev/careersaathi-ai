from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidCredentialsError,
    SocialAccountLinkingRequiredError,
    SocialAuthenticationConflictError,
)
from app.models.social_account import GITHUB_PROVIDER
from app.models.user import User
from app.repositories.social_account_repository import (
    SocialAccountRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.github_identity_service import (
    GitHubIdentity,
    retrieve_github_identity,
)
from app.services.github_oauth_service import (
    exchange_github_authorization_code,
)


def get_returning_github_user(
    social_account_repository: SocialAccountRepository,
    identity: GitHubIdentity,
) -> User | None:
    social_account = social_account_repository.get_by_provider_subject(
        GITHUB_PROVIDER,
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


def authenticate_github_user(
    session: Session,
    authorization_code: str,
    code_verifier: str,
) -> User:
    github_access_token = exchange_github_authorization_code(
        authorization_code,
        code_verifier,
    )

    identity = retrieve_github_identity(github_access_token)

    user_repository = UserRepository(session)
    social_account_repository = SocialAccountRepository(session)

    returning_user = get_returning_github_user(
        social_account_repository,
        identity,
    )

    if returning_user is not None:
        return returning_user

    existing_user = user_repository.get_by_email(identity.email)

    if existing_user is not None:
        raise SocialAccountLinkingRequiredError("GitHub")

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
            provider=GITHUB_PROVIDER,
            provider_subject=identity.subject,
            provider_email=identity.email,
        )

        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise SocialAuthenticationConflictError from exc

    session.refresh(user)

    return user
