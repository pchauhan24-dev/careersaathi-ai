from fastapi import status
from fastapi.testclient import TestClient


def test_register_candidate(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Career Saathi",
            "email": "candidate@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    payload = response.json()

    assert payload["success"] is True
    assert payload["message"] == "Account created successfully."
    assert payload["data"]["full_name"] == "Career Saathi"
    assert payload["data"]["email"] == "candidate@example.com"
    assert "password" not in payload["data"]
    assert "password_hash" not in payload["data"]


def test_register_candidate_rejects_duplicate_email(
    client: TestClient,
) -> None:
    registration_data = {
        "full_name": "Career Saathi",
        "email": "candidate@example.com",
        "password": "StrongPassword123!",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=registration_data,
    )
    second_response = client.post(
        "/api/v1/auth/register",
        json=registration_data,
    )

    assert first_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_409_CONFLICT
    assert second_response.json()["detail"] == (
        "An account with this email already exists."
    )


def test_register_candidate_rejects_invalid_data(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "A",
            "email": "invalid-email",
            "password": "short",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
