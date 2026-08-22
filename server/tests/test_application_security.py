import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


def test_trusted_host_accepts_configured_host(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/health",
        headers={
            "Host": "testserver",
        },
    )

    assert response.status_code == status.HTTP_200_OK


def test_trusted_host_rejects_unknown_host(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/health",
        headers={
            "Host": "attacker.example.com",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.text == "Invalid host header"


def test_cors_allows_configured_client_origin(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/health",
        headers={
            "Origin": settings.client_url,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["access-control-allow-origin"] == (settings.client_url)
    assert response.headers["access-control-allow-credentials"] == ("true")
    assert "Retry-After" in response.headers["access-control-expose-headers"]


def test_cors_does_not_allow_unknown_origin(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/health",
        headers={
            "Origin": "https://attacker.example.com",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access-control-allow-origin" not in response.headers


def test_api_documentation_can_be_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "api_docs_enabled",
        False,
    )

    secured_application = create_app()

    with TestClient(
        secured_application,
        base_url="http://testserver",
    ) as secured_client:
        docs_response = secured_client.get("/docs")
        redoc_response = secured_client.get("/redoc")
        openapi_response = secured_client.get("/openapi.json")
        health_response = secured_client.get("/api/v1/health")

    assert docs_response.status_code == (status.HTTP_404_NOT_FOUND)
    assert redoc_response.status_code == (status.HTTP_404_NOT_FOUND)
    assert openapi_response.status_code == (status.HTTP_404_NOT_FOUND)
    assert health_response.status_code == status.HTTP_200_OK
