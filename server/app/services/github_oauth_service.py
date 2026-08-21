import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import requests

from app.core.config import settings
from app.core.exceptions import (
    GitHubAuthenticationConfigurationError,
    GitHubAuthenticationUnavailableError,
    InvalidGitHubAuthorizationError,
)

GITHUB_AUTHORIZATION_ENDPOINT = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_ENDPOINT = "https://github.com/login/oauth/access_token"

GITHUB_REQUIRED_SCOPES = frozenset(
    {
        "read:user",
        "user:email",
    }
)

GITHUB_REQUEST_TIMEOUT_SECONDS = 10


@dataclass(frozen=True, slots=True)
class GitHubAuthorizationRequest:
    authorization_url: str
    state: str
    code_verifier: str


@dataclass(frozen=True, slots=True)
class GitHubConfiguration:
    client_id: str
    client_secret: str
    redirect_uri: str


def get_github_configuration() -> GitHubConfiguration:
    client_id = settings.github_client_id
    client_secret = settings.github_client_secret
    redirect_uri = settings.github_redirect_uri

    if client_id is None or not client_id.strip():
        raise GitHubAuthenticationConfigurationError

    if client_secret is None:
        raise GitHubAuthenticationConfigurationError

    normalized_client_secret = client_secret.get_secret_value().strip()

    if not normalized_client_secret or not redirect_uri.strip():
        raise GitHubAuthenticationConfigurationError

    return GitHubConfiguration(
        client_id=client_id.strip(),
        client_secret=normalized_client_secret,
        redirect_uri=redirect_uri.strip(),
    )


def create_pkce_challenge(code_verifier: str) -> str:
    challenge_digest = hashlib.sha256(
        code_verifier.encode("ascii"),
    ).digest()

    return base64.urlsafe_b64encode(challenge_digest).rstrip(b"=").decode("ascii")


def create_github_authorization_request() -> GitHubAuthorizationRequest:
    configuration = get_github_configuration()

    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = create_pkce_challenge(code_verifier)

    query_parameters = urlencode(
        {
            "client_id": configuration.client_id,
            "redirect_uri": configuration.redirect_uri,
            "scope": " ".join(sorted(GITHUB_REQUIRED_SCOPES)),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )

    return GitHubAuthorizationRequest(
        authorization_url=(f"{GITHUB_AUTHORIZATION_ENDPOINT}?{query_parameters}"),
        state=state,
        code_verifier=code_verifier,
    )


def normalize_returned_scopes(raw_scopes: object) -> set[str]:
    if not isinstance(raw_scopes, str):
        return set()

    return {
        scope.strip()
        for scope in raw_scopes.replace(" ", ",").split(",")
        if scope.strip()
    }


def exchange_github_authorization_code(
    code: str,
    code_verifier: str,
) -> str:
    configuration = get_github_configuration()

    normalized_code = code.strip()
    normalized_verifier = code_verifier.strip()

    if not normalized_code or not 43 <= len(normalized_verifier) <= 128:
        raise InvalidGitHubAuthorizationError

    try:
        response = requests.post(
            GITHUB_TOKEN_ENDPOINT,
            headers={
                "Accept": "application/json",
            },
            data={
                "client_id": configuration.client_id,
                "client_secret": configuration.client_secret,
                "code": normalized_code,
                "redirect_uri": configuration.redirect_uri,
                "code_verifier": normalized_verifier,
            },
            timeout=GITHUB_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise GitHubAuthenticationUnavailableError from exc

    if response.status_code >= 500:
        raise GitHubAuthenticationUnavailableError

    if response.status_code != 200:
        raise InvalidGitHubAuthorizationError

    try:
        payload = response.json()
    except ValueError as exc:
        raise InvalidGitHubAuthorizationError from exc

    if not isinstance(payload, dict) or payload.get("error") is not None:
        raise InvalidGitHubAuthorizationError

    access_token = payload.get("access_token")
    token_type = payload.get("token_type")
    returned_scopes = normalize_returned_scopes(payload.get("scope"))

    if not isinstance(access_token, str) or not access_token.strip():
        raise InvalidGitHubAuthorizationError

    if not isinstance(token_type, str) or token_type.lower() != "bearer":
        raise InvalidGitHubAuthorizationError

    if not GITHUB_REQUIRED_SCOPES.issubset(returned_scopes):
        raise InvalidGitHubAuthorizationError

    return access_token.strip()
