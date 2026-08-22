from collections.abc import Callable
from uuid import uuid4

import pytest
from fastapi import Request, status
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.routes.auth import (
    FORGOT_PASSWORD_RATE_LIMIT,
    GITHUB_AUTHORIZE_RATE_LIMIT,
    GITHUB_CALLBACK_RATE_LIMIT,
    GOOGLE_LOGIN_RATE_LIMIT,
    LOGIN_RATE_LIMIT,
    LOGOUT_RATE_LIMIT,
    REFRESH_RATE_LIMIT,
    REGISTER_RATE_LIMIT,
    RESEND_VERIFICATION_RATE_LIMIT,
    RESET_PASSWORD_RATE_LIMIT,
    VERIFY_EMAIL_RATE_LIMIT,
)
from app.api.routes.auth import (
    router as auth_router,
)
from app.core.config import settings
from app.core.rate_limit import RATE_LIMIT_ERROR_DETAIL

RATE_LIMITED_ROUTES = [
    (
        "/auth/register",
        "POST",
        REGISTER_RATE_LIMIT,
    ),
    (
        "/auth/verify-email",
        "POST",
        VERIFY_EMAIL_RATE_LIMIT,
    ),
    (
        "/auth/resend-verification",
        "POST",
        RESEND_VERIFICATION_RATE_LIMIT,
    ),
    (
        "/auth/forgot-password",
        "POST",
        FORGOT_PASSWORD_RATE_LIMIT,
    ),
    (
        "/auth/reset-password",
        "POST",
        RESET_PASSWORD_RATE_LIMIT,
    ),
    (
        "/auth/login",
        "POST",
        LOGIN_RATE_LIMIT,
    ),
    (
        "/auth/google",
        "POST",
        GOOGLE_LOGIN_RATE_LIMIT,
    ),
    (
        "/auth/github/authorize",
        "GET",
        GITHUB_AUTHORIZE_RATE_LIMIT,
    ),
    (
        "/auth/github/callback",
        "GET",
        GITHUB_CALLBACK_RATE_LIMIT,
    ),
    (
        "/auth/refresh",
        "POST",
        REFRESH_RATE_LIMIT,
    ),
    (
        "/auth/logout",
        "POST",
        LOGOUT_RATE_LIMIT,
    ),
]


def get_auth_route(
    path: str,
    method: str,
) -> APIRoute:
    for route in auth_router.routes:
        if (
            isinstance(route, APIRoute)
            and route.path == path
            and method in route.methods
        ):
            return route

    raise AssertionError(f"Authentication route not found: {method} {path}")


@pytest.mark.parametrize(
    (
        "path",
        "method",
        "expected_dependency",
    ),
    RATE_LIMITED_ROUTES,
)
def test_sensitive_auth_route_has_rate_limit(
    path: str,
    method: str,
    expected_dependency: Callable[[Request], None],
) -> None:
    route = get_auth_route(
        path,
        method,
    )

    dependency_calls = {dependency.call for dependency in route.dependant.dependencies}

    assert expected_dependency in dependency_calls


def test_login_route_rejects_excess_requests(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unique_client_identifier = f"test-client-{uuid4()}"

    def get_unique_client_identifier(
        request: Request,
    ) -> str:
        return unique_client_identifier

    monkeypatch.setattr(
        settings,
        "environment",
        "development",
    )
    monkeypatch.setattr(
        settings,
        "rate_limit_enabled",
        True,
    )
    monkeypatch.setattr(
        "app.core.rate_limit.get_client_identifier",
        get_unique_client_identifier,
    )

    login_data = {
        "email": "unknown@example.com",
        "password": "WrongPassword123!",
    }

    for _ in range(10):
        response = client.post(
            "/api/v1/auth/login",
            json=login_data,
        )

        assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    blocked_response = client.post(
        "/api/v1/auth/login",
        json=login_data,
    )

    assert blocked_response.status_code == (status.HTTP_429_TOO_MANY_REQUESTS)
    assert blocked_response.json() == {
        "detail": RATE_LIMIT_ERROR_DETAIL,
    }
    assert int(blocked_response.headers["retry-after"]) >= 1
