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
        super().__init__("Unable to send the email verification message.")
