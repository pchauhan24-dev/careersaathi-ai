from urllib.parse import parse_qs, urlparse

import pytest
import requests
from pydantic import SecretStr

from app.core.config import settings
from app.core.exceptions import (
    GitHubAuthenticationConfigurationError,
    GitHubAuthenticationUnavailableError,
    InvalidGitHubAuthorizationError,
)
from app.services.github_oauth_service import (
    GITHUB_AUTHORIZATION_ENDPOINT,
    GITHUB_TOKEN_ENDPOINT,
    create_github_authorization_request,
    create_pkce_challenge,
    exchange_github_authorization_code,
)


class SuccessfulTokenResponse:
    status_code = 200

    def json(self) -> dict[str, str]:
        return {
            "access_token": "github-access-token",
            "token_type": "bearer",
            "scope": "read:user,user:email",
        }


class InvalidTokenResponse:
    status_code = 200

    def json(self) -> dict[str, str]:
        return {
            "error": "bad_verification_code",
            "error_description": "The code is incorrect or expired.",
        }


@pytest.fixture
def github_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "github_client_id",
        "github-client-id",
    )
    monkeypatch.setattr(
        settings,
        "github_client_secret",
        SecretStr("github-client-secret"),
    )
    monkeypatch.setattr(
        settings,
        "github_redirect_uri",
        "http://localhost:8000/api/v1/auth/github/callback",
    )


def test_create_github_authorization_request(
    github_configuration: None,
) -> None:
    authorization_request = create_github_authorization_request()
    parsed_url = urlparse(authorization_request.authorization_url)
    query_parameters = parse_qs(parsed_url.query)

    assert (
        f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        == GITHUB_AUTHORIZATION_ENDPOINT
    )
    assert query_parameters["client_id"] == ["github-client-id"]
    assert query_parameters["redirect_uri"] == [
        "http://localhost:8000/api/v1/auth/github/callback"
    ]
    assert set(query_parameters["scope"][0].split()) == {
        "read:user",
        "user:email",
    }
    assert query_parameters["state"] == [authorization_request.state]
    assert query_parameters["code_challenge_method"] == ["S256"]
    assert query_parameters["code_challenge"] == [
        create_pkce_challenge(authorization_request.code_verifier)
    ]
    assert 43 <= len(authorization_request.code_verifier) <= 128


def test_github_authorization_requires_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "github_client_id", None)

    with pytest.raises(GitHubAuthenticationConfigurationError):
        create_github_authorization_request()


def test_exchange_github_authorization_code(
    github_configuration: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request: dict[str, object] = {}

    def fake_post(
        url: str,
        **kwargs: object,
    ) -> SuccessfulTokenResponse:
        captured_request["url"] = url
        captured_request.update(kwargs)

        return SuccessfulTokenResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    access_token = exchange_github_authorization_code(
        "temporary-github-code",
        "v" * 64,
    )

    assert access_token == "github-access-token"
    assert captured_request["url"] == GITHUB_TOKEN_ENDPOINT

    request_data = captured_request["data"]

    assert isinstance(request_data, dict)
    assert request_data["client_id"] == "github-client-id"
    assert request_data["client_secret"] == "github-client-secret"
    assert request_data["code"] == "temporary-github-code"
    assert request_data["code_verifier"] == "v" * 64


def test_exchange_rejects_invalid_github_response(
    github_configuration: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(
        url: str,
        **kwargs: object,
    ) -> InvalidTokenResponse:
        return InvalidTokenResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(InvalidGitHubAuthorizationError):
        exchange_github_authorization_code(
            "invalid-code",
            "v" * 64,
        )


def test_exchange_handles_github_unavailability(
    github_configuration: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(
        url: str,
        **kwargs: object,
    ) -> None:
        raise requests.ConnectionError

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(GitHubAuthenticationUnavailableError):
        exchange_github_authorization_code(
            "temporary-code",
            "v" * 64,
        )
