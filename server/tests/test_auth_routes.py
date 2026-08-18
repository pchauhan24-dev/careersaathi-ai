from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository

REGISTRATION_DATA = {
    "full_name": "Career Saathi",
    "email": "candidate@example.com",
    "password": "StrongPassword123!",
}

LOGIN_DATA = {
    "email": "candidate@example.com",
    "password": "StrongPassword123!",
}


def mark_candidate_as_verified(
    db_session: Session,
    email: str = "candidate@example.com",
) -> None:
    user = UserRepository(db_session).get_by_email(email)

    assert user is not None

    user.is_verified = True
    db_session.commit()
    db_session.refresh(user)


def test_login_candidate(
    client: TestClient,
    db_session: Session,
) -> None:
    registration_response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    assert registration_response.status_code == status.HTTP_201_CREATED

    mark_candidate_as_verified(db_session)

    login_response = client.post(
        "/api/v1/auth/login",
        json=LOGIN_DATA,
    )

    assert login_response.status_code == status.HTTP_200_OK

    payload = login_response.json()

    refresh_cookie = login_response.cookies.get(settings.refresh_cookie_name)
    set_cookie_header = login_response.headers["set-cookie"]

    assert refresh_cookie is not None
    assert "httponly" in set_cookie_header.lower()
    assert "samesite=lax" in set_cookie_header.lower()
    assert "path=/api/v1/auth" in set_cookie_header.lower()

    assert payload["success"] is True
    assert payload["data"]["token_type"] == "bearer"
    assert payload["data"]["expires_in"] == 1800
    assert payload["data"]["user"]["email"] == "candidate@example.com"

    token_payload = decode_access_token(
        payload["data"]["access_token"],
    )

    assert token_payload["sub"] == registration_response.json()["data"]["id"]


def test_login_candidate_rejects_unverified_email(
    client: TestClient,
) -> None:
    registration_response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json=LOGIN_DATA,
    )

    assert registration_response.status_code == status.HTTP_201_CREATED
    assert login_response.status_code == status.HTTP_403_FORBIDDEN
    assert login_response.json()["detail"] == (
        "Please verify your email before logging in."
    )
    assert login_response.cookies.get(settings.refresh_cookie_name) is None


def test_login_candidate_rejects_invalid_credentials(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid email or password."


def test_register_candidate(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    assert response.status_code == status.HTTP_201_CREATED

    payload = response.json()

    assert payload["success"] is True
    assert payload["message"] == (
        "Account created successfully. Please verify your email."
    )
    assert payload["data"]["full_name"] == "Career Saathi"
    assert payload["data"]["email"] == "candidate@example.com"
    assert payload["data"]["is_verified"] is False
    assert "password" not in payload["data"]
    assert "password_hash" not in payload["data"]


def test_register_candidate_rejects_duplicate_email(
    client: TestClient,
) -> None:
    first_response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )
    second_response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
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


def test_refresh_authentication_session(
    client: TestClient,
    db_session: Session,
) -> None:
    registration_response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    assert registration_response.status_code == status.HTTP_201_CREATED

    mark_candidate_as_verified(db_session)

    login_response = client.post(
        "/api/v1/auth/login",
        json=LOGIN_DATA,
    )

    old_refresh_token = login_response.cookies.get(settings.refresh_cookie_name)

    refresh_response = client.post("/api/v1/auth/refresh")

    new_refresh_token = refresh_response.cookies.get(settings.refresh_cookie_name)

    assert login_response.status_code == status.HTTP_200_OK
    assert refresh_response.status_code == status.HTTP_200_OK
    assert old_refresh_token is not None
    assert new_refresh_token is not None
    assert new_refresh_token != old_refresh_token

    payload = refresh_response.json()
    token_payload = decode_access_token(payload["data"]["access_token"])

    assert payload["success"] is True
    assert payload["message"] == "Session refreshed successfully."
    assert token_payload["sub"] == registration_response.json()["data"]["id"]


def test_refresh_rejects_missing_cookie(
    client: TestClient,
) -> None:
    client.cookies.clear()

    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == ("Invalid or expired refresh token.")


def test_logout_candidate(
    client: TestClient,
    db_session: Session,
) -> None:
    registration_response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    assert registration_response.status_code == status.HTTP_201_CREATED

    mark_candidate_as_verified(db_session)

    login_response = client.post(
        "/api/v1/auth/login",
        json=LOGIN_DATA,
    )

    assert login_response.status_code == status.HTTP_200_OK
    assert client.cookies.get(settings.refresh_cookie_name) is not None

    logout_response = client.post("/api/v1/auth/logout")

    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json() == {
        "success": True,
        "message": "Logout successful.",
    }

    set_cookie_header = logout_response.headers["set-cookie"]

    assert f"{settings.refresh_cookie_name}=" in set_cookie_header
    assert "Max-Age=0" in set_cookie_header
    assert client.cookies.get(settings.refresh_cookie_name) is None


def test_logout_without_cookie_is_idempotent(
    client: TestClient,
) -> None:
    client.cookies.clear()

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "success": True,
        "message": "Logout successful.",
    }


def test_refresh_rejects_logged_out_session(
    client: TestClient,
    db_session: Session,
) -> None:
    registration_response = client.post(
        "/api/v1/auth/register",
        json=REGISTRATION_DATA,
    )

    assert registration_response.status_code == status.HTTP_201_CREATED

    mark_candidate_as_verified(db_session)

    login_response = client.post(
        "/api/v1/auth/login",
        json=LOGIN_DATA,
    )

    old_refresh_token = login_response.cookies.get(settings.refresh_cookie_name)

    assert login_response.status_code == status.HTTP_200_OK
    assert old_refresh_token is not None

    logout_response = client.post("/api/v1/auth/logout")

    assert logout_response.status_code == status.HTTP_200_OK

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": (f"{settings.refresh_cookie_name}={old_refresh_token}")},
    )

    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert refresh_response.json()["detail"] == ("Invalid or expired refresh token.")
