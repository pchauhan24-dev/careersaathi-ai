from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyRegisteredError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegister


def register_user(
    session: Session,
    registration_data: UserRegister,
) -> User:
    repository = UserRepository(session)
    normalized_email = str(registration_data.email).lower()

    existing_user = repository.get_by_email(normalized_email)

    if existing_user is not None:
        raise EmailAlreadyRegisteredError

    user = repository.create(
        full_name=registration_data.full_name,
        email=normalized_email,
        password_hash=hash_password(registration_data.password),
    )

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise EmailAlreadyRegisteredError from exc

    session.refresh(user)

    return user
