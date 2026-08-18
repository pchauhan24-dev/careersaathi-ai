from fastapi import Response

from app.core.config import settings

REFRESH_COOKIE_PATH = "/api/v1/auth"


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
