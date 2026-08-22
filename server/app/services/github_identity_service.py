from dataclasses import dataclass
from typing import Any

import requests
from email_validator import EmailNotValidError, validate_email

from app.core.exceptions import (
    GitHubAuthenticationUnavailableError,
    InvalidGitHubAuthorizationError,
)

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"
GITHUB_REQUEST_TIMEOUT_SECONDS = 10


@dataclass(frozen=True, slots=True)
class GitHubIdentity:
    subject: str
    email: str
    full_name: str


def create_github_api_headers(
    access_token: str,
) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {access_token}",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": "CareerSaathi-AI",
    }


def request_github_json(
    endpoint: str,
    access_token: str,
) -> Any:
    try:
        response = requests.get(
            f"{GITHUB_API_BASE_URL}{endpoint}",
            headers=create_github_api_headers(access_token),
            timeout=GITHUB_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise GitHubAuthenticationUnavailableError from exc

    if response.status_code >= 500:
        raise GitHubAuthenticationUnavailableError

    if response.status_code != 200:
        raise InvalidGitHubAuthorizationError

    try:
        return response.json()
    except ValueError as exc:
        raise InvalidGitHubAuthorizationError from exc


def get_verified_primary_email(
    email_payload: Any,
) -> str:
    if not isinstance(email_payload, list):
        raise InvalidGitHubAuthorizationError

    primary_email = next(
        (
            email_record.get("email")
            for email_record in email_payload
            if isinstance(email_record, dict)
            and email_record.get("primary") is True
            and email_record.get("verified") is True
        ),
        None,
    )

    if not isinstance(primary_email, str):
        raise InvalidGitHubAuthorizationError

    try:
        email_information = validate_email(
            primary_email,
            check_deliverability=False,
        )
    except EmailNotValidError as exc:
        raise InvalidGitHubAuthorizationError from exc

    return email_information.normalized.lower()


def normalize_github_name(
    raw_name: Any,
    raw_login: Any,
    email: str,
) -> str:
    normalized_name = " ".join(raw_name.split()) if isinstance(raw_name, str) else ""

    if len(normalized_name) < 2 and isinstance(raw_login, str):
        normalized_name = " ".join(
            raw_login.replace("-", " ").replace("_", " ").split()
        )

    if len(normalized_name) < 2:
        email_name = email.split("@", maxsplit=1)[0]
        normalized_name = " ".join(
            email_name.replace(".", " ").replace("_", " ").split()
        )

    if len(normalized_name) < 2:
        normalized_name = "GitHub User"

    return normalized_name[:120]


def retrieve_github_identity(
    access_token: str,
) -> GitHubIdentity:
    normalized_access_token = access_token.strip()

    if not normalized_access_token:
        raise InvalidGitHubAuthorizationError

    profile_payload = request_github_json(
        "/user",
        normalized_access_token,
    )
    email_payload = request_github_json(
        "/user/emails",
        normalized_access_token,
    )

    if not isinstance(profile_payload, dict):
        raise InvalidGitHubAuthorizationError

    user_id = profile_payload.get("id")

    if not isinstance(user_id, int) or user_id <= 0:
        raise InvalidGitHubAuthorizationError

    normalized_email = get_verified_primary_email(email_payload)
    full_name = normalize_github_name(
        profile_payload.get("name"),
        profile_payload.get("login"),
        normalized_email,
    )

    return GitHubIdentity(
        subject=str(user_id),
        email=normalized_email,
        full_name=full_name,
    )
