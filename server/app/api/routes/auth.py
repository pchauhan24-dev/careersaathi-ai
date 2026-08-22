import secrets
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
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookies import (
    GITHUB_OAUTH_STATE_COOKIE_NAME,
    GITHUB_OAUTH_VERIFIER_COOKIE_NAME,
    clear_github_oauth_cookies,
    clear_refresh_cookie,
    set_github_oauth_cookies,
    set_refresh_cookie,
)
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    GitHubAuthenticationConfigurationError,
    GitHubAuthenticationUnavailableError,
    GoogleAuthenticationConfigurationError,
    InvalidCredentialsError,
    InvalidEmailVerificationTokenError,
    InvalidGitHubAuthorizationError,
    InvalidGoogleCredentialError,
    InvalidPasswordResetTokenError,
    InvalidRefreshTokenError,
    SocialAccountLinkingRequiredError,
    SocialAuthenticationConflictError,
)
from app.core.rate_limit import create_rate_limit_dependency
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import (
    AccessTokenData,
    EmailVerificationRequest,
    EmailVerificationResponse,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginResponse,
    LogoutResponse,
    MessageResponse,
    RegisterResponse,
    ResendEmailVerificationRequest,
    ResetPasswordRequest,
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
from app.services.email_service import (
    send_password_reset_email,
    send_verification_email,
)
from app.services.email_verification_service import (
    create_email_verification_token,
    request_email_verification,
    verify_email_verification_token,
)
from app.services.github_auth_service import authenticate_github_user
from app.services.github_oauth_service import (
    create_github_authorization_request,
)
from app.services.google_auth_service import authenticate_google_user
from app.services.password_reset_service import (
    request_password_reset,
    reset_user_password,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

REGISTER_RATE_LIMIT = create_rate_limit_dependency(
    "5/hour",
    "auth-register",
)
VERIFY_EMAIL_RATE_LIMIT = create_rate_limit_dependency(
    "10/minute",
    "auth-verify-email",
)
RESEND_VERIFICATION_RATE_LIMIT = create_rate_limit_dependency(
    "3/minute",
    "auth-resend-verification",
)
FORGOT_PASSWORD_RATE_LIMIT = create_rate_limit_dependency(
    "3/minute",
    "auth-forgot-password",
)
RESET_PASSWORD_RATE_LIMIT = create_rate_limit_dependency(
    "5/minute",
    "auth-reset-password",
)
LOGIN_RATE_LIMIT = create_rate_limit_dependency(
    "10/minute",
    "auth-login",
)
GOOGLE_LOGIN_RATE_LIMIT = create_rate_limit_dependency(
    "10/minute",
    "auth-google",
)
GITHUB_AUTHORIZE_RATE_LIMIT = create_rate_limit_dependency(
    "10/minute",
    "auth-github-authorize",
)
GITHUB_CALLBACK_RATE_LIMIT = create_rate_limit_dependency(
    "20/minute",
    "auth-github-callback",
)
REFRESH_RATE_LIMIT = create_rate_limit_dependency(
    "30/minute",
    "auth-refresh",
)
LOGOUT_RATE_LIMIT = create_rate_limit_dependency(
    "30/minute",
    "auth-logout",
)


def create_github_error_response(
    status_code: int,
    detail: str,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={"detail": detail},
    )

    clear_github_oauth_cookies(response)

    return response


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(REGISTER_RATE_LIMIT)],
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
    dependencies=[Depends(VERIFY_EMAIL_RATE_LIMIT)],
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
    dependencies=[Depends(RESEND_VERIFICATION_RATE_LIMIT)],
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
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[Depends(FORGOT_PASSWORD_RATE_LIMIT)],
    summary="Request a password reset message",
)
def forgot_candidate_password(
    forgot_password_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    reset_request = request_password_reset(
        session,
        str(forgot_password_data.email),
    )

    if reset_request is not None:
        user, raw_reset_token = reset_request

        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            user.full_name,
            raw_reset_token,
        )

    return MessageResponse(
        success=True,
        message=(
            "If an active account exists for this email, "
            "a password reset message will be sent."
        ),
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    dependencies=[Depends(RESET_PASSWORD_RATE_LIMIT)],
    summary="Reset a candidate password",
)
def reset_candidate_password(
    reset_password_data: ResetPasswordRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    try:
        reset_user_password(
            session,
            reset_password_data.token,
            reset_password_data.new_password,
        )
    except InvalidPasswordResetTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    clear_refresh_cookie(response)

    return MessageResponse(
        success=True,
        message="Password reset successfully. Please log in again.",
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    dependencies=[Depends(LOGIN_RATE_LIMIT)],
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
            expires_in=(settings.access_token_expire_minutes * 60),
            user=UserResponse.model_validate(user),
        ),
    )


@router.post(
    "/google",
    response_model=LoginResponse,
    dependencies=[Depends(GOOGLE_LOGIN_RATE_LIMIT)],
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
            expires_in=(settings.access_token_expire_minutes * 60),
            user=UserResponse.model_validate(user),
        ),
    )


@router.get(
    "/github/authorize",
    dependencies=[Depends(GITHUB_AUTHORIZE_RATE_LIMIT)],
    summary="Begin GitHub authentication",
)
def begin_github_authentication() -> RedirectResponse:
    try:
        authorization_request = create_github_authorization_request()
    except GitHubAuthenticationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    response = RedirectResponse(
        url=authorization_request.authorization_url,
        status_code=status.HTTP_302_FOUND,
    )

    set_github_oauth_cookies(
        response,
        authorization_request.state,
        authorization_request.code_verifier,
    )

    return response


@router.get(
    "/github/callback",
    dependencies=[Depends(GITHUB_CALLBACK_RATE_LIMIT)],
    summary="Complete GitHub authentication",
)
def complete_github_authentication(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> Response:
    stored_state = request.cookies.get(GITHUB_OAUTH_STATE_COOKIE_NAME)
    code_verifier = request.cookies.get(GITHUB_OAUTH_VERIFIER_COOKIE_NAME)

    state_is_invalid = (
        state is None
        or stored_state is None
        or not state.strip()
        or len(state) > 512
        or not secrets.compare_digest(state, stored_state)
    )

    if state_is_invalid:
        return create_github_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired GitHub authorization.",
        )

    if error is not None:
        return create_github_error_response(
            status.HTTP_400_BAD_REQUEST,
            "GitHub authorization was cancelled or denied.",
        )

    authorization_is_invalid = (
        code is None or code_verifier is None or not code.strip() or len(code) > 2048
    )

    if authorization_is_invalid:
        return create_github_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired GitHub authorization.",
        )

    try:
        user = authenticate_github_user(
            session,
            code,
            code_verifier,
        )
    except GitHubAuthenticationConfigurationError as exc:
        return create_github_error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            str(exc),
        )
    except GitHubAuthenticationUnavailableError as exc:
        return create_github_error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            str(exc),
        )
    except (
        InvalidCredentialsError,
        InvalidGitHubAuthorizationError,
    ):
        return create_github_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Unable to authenticate with GitHub.",
        )
    except SocialAccountLinkingRequiredError as exc:
        return create_github_error_response(
            status.HTTP_409_CONFLICT,
            str(exc),
        )
    except SocialAuthenticationConflictError as exc:
        return create_github_error_response(
            status.HTTP_409_CONFLICT,
            str(exc),
        )

    _, raw_refresh_token = create_refresh_session(
        session,
        user.id,
    )

    client_redirect_url = f"{settings.client_url.rstrip('/')}/login?github=success"

    response = RedirectResponse(
        url=client_redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )

    clear_github_oauth_cookies(response)

    set_refresh_cookie(
        response,
        raw_refresh_token,
    )

    return response


@router.post(
    "/refresh",
    response_model=LoginResponse,
    dependencies=[Depends(REFRESH_RATE_LIMIT)],
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
            expires_in=(settings.access_token_expire_minutes * 60),
            user=UserResponse.model_validate(user),
        ),
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    dependencies=[Depends(LOGOUT_RATE_LIMIT)],
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
