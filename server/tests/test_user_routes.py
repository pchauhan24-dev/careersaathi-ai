from datetime import timedelta
from uuid import UUID, uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User

REGISTRATION_DATA = {
    "full_name": "Career Saathi",
    "email": "candidate@example.com",
    "password": "StrongPassword123!",
}


def register_and_login(
    client: TestClient,
) -> tuple[dict, str]:
    registration_response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": REGISTRATION_DATA["email"],
            "password": REGISTRATION_DATA["password"],
        },
    )

    assert registration_response.status_code == status.HTTP_201_CREATED
    assert login_response.status_code == status.HTTP_200_OK

    user_data = registration_response.json()["data"]
    access_token = login_response.json()["data"]["access_token"]

    return user_data, access_token


def test_get_current_user(
    client: TestClient,
) -> None:
    user_data, access_token = register_and_login(client)

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_200_OK

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["id"] == user_data["id"]
    assert payload["data"]["email"] == user_data["email"]
    assert "password_hash" not in payload["data"]


def test_get_current_user_rejects_missing_token(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == ("Could not validate credentials.")


def test_get_current_user_rejects_invalid_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_rejects_expired_token(
    client: TestClient,
) -> None:
    user_data, _ = register_and_login(client)

    expired_token = create_access_token(
        user_data["id"],
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_rejects_unknown_user(
    client: TestClient,
) -> None:
    access_token = create_access_token(str(uuid4()))

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_rejects_inactive_user(
    client: TestClient,
    db_session: Session,
) -> None:
    user_data, access_token = register_and_login(client)

    user = db_session.get(
        User,
        UUID(user_data["id"]),
    )

    assert user is not None

    user.is_active = False
    db_session.commit()

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
