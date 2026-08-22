import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookies import (
    GITHUB_OAUTH_STATE_COOKIE_NAME,
    GITHUB_OAUTH_VERIFIER_COOKIE_NAME,
)
from app.core.exceptions import (
    GitHubAuthenticationConfigurationError,
    GitHubAuthenticationUnavailableError,
    SocialAccountLinkingRequiredError,
)
from app.repositories.user_repository import UserRepository
from app.services.github_oauth_service import (
    GitHubAuthorizationRequest,
)


def configure_github_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_authorization_request() -> GitHubAuthorizationRequest:
        return GitHubAuthorizationRequest(
            authorization_url=(
                "https://github.com/login/oauth/authorize?client_id=github-client-id"
            ),
            state="secure-github-state",
            code_verifier="v" * 64,
        )

    monkeypatch.setattr(
        "app.api.routes.auth.create_github_authorization_request",
        fake_authorization_request,
    )


def create_test_github_user(
    db_session: Session,
):
    user = UserRepository(db_session).create(
        full_name="Career Saathi",
        email="candidate@example.com",
        password_hash=None,
        is_verified=True,
    )

    db_session.commit()
    db_session.refresh(user)

    return user


def begin_test_github_authorization(
    client: TestClient,
):
    return client.get(
        "/api/v1/auth/github/authorize",
        follow_redirects=False,
    )


def test_begin_github_authentication(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_authorization(monkeypatch)

    response = begin_test_github_authorization(client)

    assert response.status_code == status.HTTP_302_FOUND
    assert response.headers["location"].startswith(
        "https://github.com/login/oauth/authorize"
    )
    assert client.cookies.get(GITHUB_OAUTH_STATE_COOKIE_NAME) == "secure-github-state"
    assert client.cookies.get(GITHUB_OAUTH_VERIFIER_COOKIE_NAME) == "v" * 64

    set_cookie_header = response.headers["set-cookie"].lower()

    assert "httponly" in set_cookie_header
    assert "samesite=lax" in set_cookie_header


def test_begin_github_authentication_requires_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_configuration_error() -> None:
        raise GitHubAuthenticationConfigurationError

    monkeypatch.setattr(
        "app.api.routes.auth.create_github_authorization_request",
        raise_configuration_error,
    )

    response = begin_test_github_authorization(client)

    assert response.status_code == (status.HTTP_503_SERVICE_UNAVAILABLE)
    assert response.json()["detail"] == ("GitHub authentication is not configured.")


def test_complete_github_authentication(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_authorization(monkeypatch)
    user = create_test_github_user(db_session)

    def fake_authenticate(
        session: Session,
        authorization_code: str,
        code_verifier: str,
    ):
        assert session is db_session
        assert authorization_code == "temporary-github-code"
        assert code_verifier == "v" * 64

        return user

    monkeypatch.setattr(
        "app.api.routes.auth.authenticate_github_user",
        fake_authenticate,
    )

    begin_response = begin_test_github_authorization(client)

    assert begin_response.status_code == status.HTTP_302_FOUND

    callback_response = client.get(
        "/api/v1/auth/github/callback",
        params={
            "code": "temporary-github-code",
            "state": "secure-github-state",
        },
        follow_redirects=False,
    )

    assert callback_response.status_code == (status.HTTP_303_SEE_OTHER)
    assert callback_response.headers["location"] == (
        f"{settings.client_url}/login?github=success"
    )

    assert client.cookies.get(GITHUB_OAUTH_STATE_COOKIE_NAME) is None
    assert client.cookies.get(GITHUB_OAUTH_VERIFIER_COOKIE_NAME) is None
    assert client.cookies.get(settings.refresh_cookie_name) is not None

    refresh_response = client.post("/api/v1/auth/refresh")

    assert refresh_response.status_code == status.HTTP_200_OK
    assert refresh_response.json()["data"]["user"]["email"] == ("candidate@example.com")


def test_github_callback_rejects_invalid_state(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_authorization(monkeypatch)
    begin_test_github_authorization(client)

    response = client.get(
        "/api/v1/auth/github/callback",
        params={
            "code": "temporary-github-code",
            "state": "incorrect-state",
        },
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == ("Invalid or expired GitHub authorization.")
    assert client.cookies.get(GITHUB_OAUTH_STATE_COOKIE_NAME) is None
    assert client.cookies.get(GITHUB_OAUTH_VERIFIER_COOKIE_NAME) is None


def test_github_callback_handles_denied_authorization(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_authorization(monkeypatch)
    begin_test_github_authorization(client)

    response = client.get(
        "/api/v1/auth/github/callback",
        params={
            "error": "access_denied",
            "state": "secure-github-state",
        },
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == (
        "GitHub authorization was cancelled or denied."
    )


def test_github_callback_requires_safe_account_linking(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_authorization(monkeypatch)

    def raise_linking_error(
        session: Session,
        authorization_code: str,
        code_verifier: str,
    ) -> None:
        raise SocialAccountLinkingRequiredError("GitHub")

    monkeypatch.setattr(
        "app.api.routes.auth.authenticate_github_user",
        raise_linking_error,
    )

    begin_test_github_authorization(client)

    response = client.get(
        "/api/v1/auth/github/callback",
        params={
            "code": "temporary-github-code",
            "state": "secure-github-state",
        },
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == (
        "An account already exists with this email. "
        "Log in using the existing method before linking GitHub."
    )


def test_github_callback_handles_provider_unavailability(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_authorization(monkeypatch)

    def raise_unavailable_error(
        session: Session,
        authorization_code: str,
        code_verifier: str,
    ) -> None:
        raise GitHubAuthenticationUnavailableError

    monkeypatch.setattr(
        "app.api.routes.auth.authenticate_github_user",
        raise_unavailable_error,
    )

    begin_test_github_authorization(client)

    response = client.get(
        "/api/v1/auth/github/callback",
        params={
            "code": "temporary-github-code",
            "state": "secure-github-state",
        },
        follow_redirects=False,
    )

    assert response.status_code == (status.HTTP_503_SERVICE_UNAVAILABLE)
    assert response.json()["detail"] == (
        "GitHub authentication is temporarily unavailable."
    )
