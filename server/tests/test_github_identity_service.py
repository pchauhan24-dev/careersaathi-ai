from typing import Any

import pytest
import requests

from app.core.exceptions import (
    GitHubAuthenticationUnavailableError,
    InvalidGitHubAuthorizationError,
)
from app.services.github_identity_service import (
    GITHUB_API_BASE_URL,
    GitHubIdentity,
    retrieve_github_identity,
)


class GitHubResponse:
    def __init__(
        self,
        payload: Any,
        status_code: int = 200,
    ) -> None:
        self.payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        return self.payload


def test_retrieve_github_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(
        url: str,
        **kwargs: object,
    ) -> GitHubResponse:
        if url == f"{GITHUB_API_BASE_URL}/user":
            return GitHubResponse(
                {
                    "id": 123456,
                    "login": "career-saathi",
                    "name": "  Career   Saathi  ",
                    "email": None,
                }
            )

        if url == f"{GITHUB_API_BASE_URL}/user/emails":
            return GitHubResponse(
                [
                    {
                        "email": "secondary@example.com",
                        "primary": False,
                        "verified": True,
                    },
                    {
                        "email": "Candidate@Example.com",
                        "primary": True,
                        "verified": True,
                    },
                ]
            )

        raise AssertionError(f"Unexpected GitHub URL: {url}")

    monkeypatch.setattr(requests, "get", fake_get)

    identity = retrieve_github_identity("github-access-token")

    assert identity == GitHubIdentity(
        subject="123456",
        email="candidate@example.com",
        full_name="Career Saathi",
    )


def test_github_identity_uses_login_as_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(
        url: str,
        **kwargs: object,
    ) -> GitHubResponse:
        if url.endswith("/user"):
            return GitHubResponse(
                {
                    "id": 789,
                    "login": "career-saathi-user",
                    "name": None,
                }
            )

        return GitHubResponse(
            [
                {
                    "email": "candidate@example.com",
                    "primary": True,
                    "verified": True,
                }
            ]
        )

    monkeypatch.setattr(requests, "get", fake_get)

    identity = retrieve_github_identity("github-access-token")

    assert identity.full_name == "career saathi user"


def test_github_identity_rejects_unverified_primary_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(
        url: str,
        **kwargs: object,
    ) -> GitHubResponse:
        if url.endswith("/user"):
            return GitHubResponse(
                {
                    "id": 123,
                    "login": "candidate",
                    "name": "Career Saathi",
                }
            )

        return GitHubResponse(
            [
                {
                    "email": "candidate@example.com",
                    "primary": True,
                    "verified": False,
                }
            ]
        )

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(InvalidGitHubAuthorizationError):
        retrieve_github_identity("github-access-token")


def test_github_identity_rejects_invalid_access_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(
        url: str,
        **kwargs: object,
    ) -> GitHubResponse:
        return GitHubResponse(
            {"message": "Bad credentials"},
            status_code=401,
        )

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(InvalidGitHubAuthorizationError):
        retrieve_github_identity("invalid-access-token")


def test_github_identity_handles_github_unavailability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(
        url: str,
        **kwargs: object,
    ) -> None:
        raise requests.ConnectionError

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(GitHubAuthenticationUnavailableError):
        retrieve_github_identity("github-access-token")
