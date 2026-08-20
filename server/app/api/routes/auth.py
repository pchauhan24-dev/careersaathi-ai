from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
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
    EmailNotVerifiedError,
    GoogleAuthenticationConfigurationError,
    InvalidCredentialsError,
    InvalidEmailVerificationTokenError,
    InvalidGoogleCredentialError,
    InvalidRefreshTokenError,
    SocialAccountLinkingRequiredError,
    SocialAuthenticationConflictError,
)
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import (
    AccessTokenData,
    EmailVerificationRequest,
    EmailVerificationResponse,
    GoogleLoginRequest,
    LoginResponse,
    LogoutResponse,
    MessageResponse,
    RegisterResponse,
    ResendEmailVerificationRequest,
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
from app.services.email_service import send_verification_email
from app.services.email_verification_service import (
    create_email_verification_token,
    request_email_verification,
    verify_email_verification_token,
)
from app.services.google_auth_service import authenticate_google_user

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
    background_tasks: BackgroundTasks,
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

    _, raw_verification_token = create_email_verification_token(
        session,
        user.id,
    )

    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.full_name,
        raw_verification_token,
    )

    return RegisterResponse(
        success=True,
        message="Account created successfully. Please verify your email.",
        data=UserResponse.model_validate(user),
    )


@router.post(
    "/verify-email",
    response_model=EmailVerificationResponse,
    summary="Verify a candidate email address",
)
def verify_candidate_email(
    verification_data: EmailVerificationRequest,
    session: Annotated[Session, Depends(get_db)],
) -> EmailVerificationResponse:
    try:
        user = verify_email_verification_token(
            session,
            verification_data.token,
        )
    except InvalidEmailVerificationTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return EmailVerificationResponse(
        success=True,
        message="Email verified successfully.",
        data=UserResponse.model_validate(user),
    )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Request another email verification message",
)
def resend_candidate_email_verification(
    resend_data: ResendEmailVerificationRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    verification_request = request_email_verification(
        session,
        str(resend_data.email),
    )

    if verification_request is not None:
        user, raw_verification_token = verification_request

        background_tasks.add_task(
            send_verification_email,
            user.email,
            user.full_name,
            raw_verification_token,
        )

    return MessageResponse(
        success=True,
        message=(
            "If an unverified account exists for this email, "
            "a verification message will be sent."
        ),
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
    except EmailNotVerifiedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
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
    "/google",
    response_model=LoginResponse,
    summary="Log in or register using Google",
)
def login_candidate_with_google(
    google_data: GoogleLoginRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    try:
        user = authenticate_google_user(
            session,
            google_data.credential,
        )
    except GoogleAuthenticationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except (
        InvalidCredentialsError,
        InvalidGoogleCredentialError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to authenticate with Google.",
        ) from exc
    except SocialAccountLinkingRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except SocialAuthenticationConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
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
        message="Google login successful.",
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
