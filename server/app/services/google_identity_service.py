from dataclasses import dataclass
from typing import Any

from email_validator import EmailNotValidError, validate_email
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings
from app.core.exceptions import (
    GoogleAuthenticationConfigurationError,
    InvalidGoogleCredentialError,
)

GOOGLE_ISSUERS = {
    "accounts.google.com",
    "https://accounts.google.com",
}


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    subject: str
    email: str
    full_name: str


def normalize_google_name(
    raw_name: Any,
    email: str,
) -> str:
    normalized_name = " ".join(raw_name.split()) if isinstance(raw_name, str) else ""

    if len(normalized_name) < 2:
        email_name = email.split("@", maxsplit=1)[0]

        normalized_name = " ".join(
            email_name.replace(".", " ").replace("_", " ").split()
        )

    if len(normalized_name) < 2:
        normalized_name = "Google User"

    return normalized_name[:120]


def verify_google_credential(
    credential: str,
) -> GoogleIdentity:
    client_id = settings.google_client_id

    if client_id is None or not client_id.strip():
        raise GoogleAuthenticationConfigurationError

    try:
        claims = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
        )
    except (GoogleAuthError, ValueError) as exc:
        raise InvalidGoogleCredentialError from exc

    issuer = claims.get("iss")
    subject = claims.get("sub")
    raw_email = claims.get("email")
    email_verified = claims.get("email_verified")

    if issuer not in GOOGLE_ISSUERS:
        raise InvalidGoogleCredentialError

    if not isinstance(subject, str) or not subject.strip() or len(subject) > 255:
        raise InvalidGoogleCredentialError

    if not (
        email_verified is True
        or (isinstance(email_verified, str) and email_verified.lower() == "true")
    ):
        raise InvalidGoogleCredentialError

    if not isinstance(raw_email, str):
        raise InvalidGoogleCredentialError

    try:
        email_information = validate_email(
            raw_email,
            check_deliverability=False,
        )
    except EmailNotValidError as exc:
        raise InvalidGoogleCredentialError from exc

    normalized_email = email_information.normalized.lower()
    full_name = normalize_google_name(
        claims.get("name"),
        normalized_email,
    )

    return GoogleIdentity(
        subject=subject.strip(),
        email=normalized_email,
        full_name=full_name,
    )
