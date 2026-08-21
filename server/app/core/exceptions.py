class EmailAlreadyRegisteredError(Exception):
    def __init__(self) -> None:
        super().__init__("An account with this email already exists.")


class InvalidCredentialsError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid email or password.")


class EmailNotVerifiedError(Exception):
    def __init__(self) -> None:
        super().__init__("Please verify your email before logging in.")


class InvalidRefreshTokenError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid or expired refresh token.")


class InvalidEmailVerificationTokenError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid or expired email verification token.")


class EmailDeliveryError(Exception):
    def __init__(self) -> None:
        super().__init__("Unable to send the email message.")


class GoogleAuthenticationConfigurationError(Exception):
    def __init__(self) -> None:
        super().__init__("Google authentication is not configured.")


class InvalidGoogleCredentialError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid Google authentication credential.")


class GitHubAuthenticationConfigurationError(Exception):
    def __init__(self) -> None:
        super().__init__("GitHub authentication is not configured.")


class InvalidGitHubAuthorizationError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid or expired GitHub authorization.")


class GitHubAuthenticationUnavailableError(Exception):
    def __init__(self) -> None:
        super().__init__("GitHub authentication is temporarily unavailable.")


class SocialAccountLinkingRequiredError(Exception):
    def __init__(
        self,
        provider: str = "Google",
    ) -> None:
        super().__init__(
            "An account already exists with this email. "
            f"Log in using the existing method before linking {provider}."
        )


class SocialAuthenticationConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("Unable to complete social authentication. Please try again.")


class InvalidPasswordResetTokenError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid or expired password reset token.")
