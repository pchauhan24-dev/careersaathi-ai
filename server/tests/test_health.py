import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["status"] == "healthy"
    assert payload["data"]["environment"] == "development"


def test_database_health_check(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.health.check_database_connection",
        lambda: None,
    )

    response = client.get("/api/v1/health/database")

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["status"] == "connected"
