from fastapi import Response

from app.core.config import settings

REFRESH_COOKIE_PATH = "/api/v1/auth"

GITHUB_OAUTH_COOKIE_PATH = "/api/v1/auth/github"
GITHUB_OAUTH_STATE_COOKIE_NAME = "careersaathi_github_oauth_state"
GITHUB_OAUTH_VERIFIER_COOKIE_NAME = "careersaathi_github_oauth_verifier"
GITHUB_OAUTH_COOKIE_MAX_AGE_SECONDS = 10 * 60


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
) -> None:
    max_age = settings.refresh_token_expire_days * 24 * 60 * 60

    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=REFRESH_COOKIE_PATH,
    )


def set_github_oauth_cookies(
    response: Response,
    state: str,
    code_verifier: str,
) -> None:
    cookie_options = {
        "max_age": GITHUB_OAUTH_COOKIE_MAX_AGE_SECONDS,
        "httponly": True,
        "secure": settings.refresh_cookie_secure,
        "samesite": "lax",
        "path": GITHUB_OAUTH_COOKIE_PATH,
    }

    response.set_cookie(
        key=GITHUB_OAUTH_STATE_COOKIE_NAME,
        value=state,
        **cookie_options,
    )
    response.set_cookie(
        key=GITHUB_OAUTH_VERIFIER_COOKIE_NAME,
        value=code_verifier,
        **cookie_options,
    )


def clear_github_oauth_cookies(
    response: Response,
) -> None:
    cookie_options = {
        "httponly": True,
        "secure": settings.refresh_cookie_secure,
        "samesite": "lax",
        "path": GITHUB_OAUTH_COOKIE_PATH,
    }

    response.delete_cookie(
        key=GITHUB_OAUTH_STATE_COOKIE_NAME,
        **cookie_options,
    )
    response.delete_cookie(
        key=GITHUB_OAUTH_VERIFIER_COOKIE_NAME,
        **cookie_options,
    )
