class EmailAlreadyRegisteredError(Exception):
    def __init__(self) -> None:
        super().__init__("An account with this email already exists.")


class InvalidCredentialsError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid email or password.")
