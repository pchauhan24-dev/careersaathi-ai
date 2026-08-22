from fastapi import Response

from app.core.cookies import (
    GITHUB_OAUTH_COOKIE_MAX_AGE_SECONDS,
    GITHUB_OAUTH_COOKIE_PATH,
    GITHUB_OAUTH_STATE_COOKIE_NAME,
    GITHUB_OAUTH_VERIFIER_COOKIE_NAME,
    clear_github_oauth_cookies,
    set_github_oauth_cookies,
)


def get_set_cookie_headers(
    response: Response,
) -> list[str]:
    return [
        header_value.decode("latin-1")
        for header_name, header_value in response.raw_headers
        if header_name.lower() == b"set-cookie"
    ]


def test_set_github_oauth_cookies() -> None:
    response = Response()

    set_github_oauth_cookies(
        response,
        "secure-oauth-state",
        "v" * 64,
    )

    cookie_headers = get_set_cookie_headers(response)

    state_cookie = next(
        header
        for header in cookie_headers
        if header.startswith(f"{GITHUB_OAUTH_STATE_COOKIE_NAME}=")
    )
    verifier_cookie = next(
        header
        for header in cookie_headers
        if header.startswith(f"{GITHUB_OAUTH_VERIFIER_COOKIE_NAME}=")
    )

    for cookie_header in (state_cookie, verifier_cookie):
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header
        assert f"Path={GITHUB_OAUTH_COOKIE_PATH}" in cookie_header
        assert f"Max-Age={GITHUB_OAUTH_COOKIE_MAX_AGE_SECONDS}" in cookie_header

    assert "secure-oauth-state" in state_cookie
    assert "v" * 64 in verifier_cookie


def test_clear_github_oauth_cookies() -> None:
    response = Response()

    clear_github_oauth_cookies(response)

    cookie_headers = get_set_cookie_headers(response)

    assert len(cookie_headers) == 2

    for cookie_header in cookie_headers:
        assert "Max-Age=0" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header
        assert f"Path={GITHUB_OAUTH_COOKIE_PATH}" in cookie_header
