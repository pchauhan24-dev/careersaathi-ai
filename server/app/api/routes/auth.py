from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import (
    AccessTokenData,
    LoginResponse,
    RegisterResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    register_user,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new candidate",
)
def register_candidate(
    registration_data: UserRegister,
    session: Annotated[Session, Depends(get_db)],
) -> RegisterResponse:
    try:
        user = register_user(
            session,
            registration_data,
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return RegisterResponse(
        success=True,
        message="Account created successfully.",
        data=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in a candidate",
)
def login_candidate(
    login_data: UserLogin,
    session: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    try:
        user = authenticate_user(
            session,
            login_data,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    access_token = create_access_token(str(user.id))

    return LoginResponse(
        success=True,
        message="Login successful.",
        data=AccessTokenData(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user),
        ),
    )
