import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


def test_api_responses_include_security_headers(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["x-content-type-options"] == ("nosniff")
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == (
        "camera=(), microphone=(), geolocation=()"
    )


def test_authentication_responses_are_not_cached(
    client: TestClient,
) -> None:
    client.cookies.clear()

    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)
    assert response.headers["cache-control"] == ("no-store, max-age=0")
    assert response.headers["pragma"] == "no-cache"


def test_user_responses_are_not_cached(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)
    assert response.headers["cache-control"] == ("no-store, max-age=0")


def test_development_responses_do_not_include_hsts(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/health")

    assert "strict-transport-security" not in response.headers


def test_production_responses_include_hsts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "environment",
        "production",
    )

    production_application = create_app()

    with TestClient(
        production_application,
        base_url="https://testserver",
    ) as production_client:
        response = production_client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["strict-transport-security"] == (
        "max-age=31536000; includeSubDomains"
    )
