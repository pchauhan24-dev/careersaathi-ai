from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookies import (
    clear_refresh_cookie,
    set_refresh_cookie,
)
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import (
    AccessTokenData,
    LoginResponse,
    LogoutResponse,
    RegisterResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    register_user,
)
from app.services.auth_session_service import (
    create_refresh_session,
    revoke_refresh_session,
    rotate_refresh_session,
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
    response: Response,
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

    _, raw_refresh_token = create_refresh_session(
        session,
        user.id,
    )

    set_refresh_cookie(
        response,
        raw_refresh_token,
    )

    return LoginResponse(
        success=True,
        message="Login successful.",
        data=AccessTokenData(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user),
        ),
    )


@router.post(
    "/refresh",
    response_model=LoginResponse,
    summary="Refresh the authentication session",
)
def refresh_authentication_session(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    raw_refresh_token = request.cookies.get(settings.refresh_cookie_name)

    if raw_refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    try:
        user, _, new_raw_refresh_token = rotate_refresh_session(
            session,
            raw_refresh_token,
        )
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    access_token = create_access_token(str(user.id))

    set_refresh_cookie(
        response,
        new_raw_refresh_token,
    )

    return LoginResponse(
        success=True,
        message="Session refreshed successfully.",
        data=AccessTokenData(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user),
        ),
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Log out the current candidate",
)
def logout_candidate(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> LogoutResponse:
    raw_refresh_token = request.cookies.get(settings.refresh_cookie_name)

    if raw_refresh_token is not None:
        revoke_refresh_session(
            session,
            raw_refresh_token,
        )

    clear_refresh_cookie(response)

    return LogoutResponse(
        success=True,
        message="Logout successful.",
    )
