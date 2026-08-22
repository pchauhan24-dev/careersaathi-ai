from collections.abc import Awaitable, Callable

from starlette.datastructures import MutableHeaders
from starlette.types import Message, Receive, Scope, Send

ASGIApplication = Callable[
    [Scope, Receive, Send],
    Awaitable[None],
]


class SecurityHeadersMiddleware:
    def __init__(
        self,
        app: ASGIApplication,
        *,
        environment: str,
        sensitive_path_prefixes: tuple[str, ...],
    ) -> None:
        self.app = app
        self.environment = environment
        self.sensitive_path_prefixes = sensitive_path_prefixes

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(
                scope,
                receive,
                send,
            )
            return

        path = str(scope.get("path", ""))

        async def send_with_security_headers(
            message: Message,
        ) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)

                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = (
                    "camera=(), microphone=(), geolocation=()"
                )

                if path.startswith(self.sensitive_path_prefixes):
                    headers["Cache-Control"] = "no-store, max-age=0"
                    headers["Pragma"] = "no-cache"

                if self.environment == "production":
                    headers["Strict-Transport-Security"] = (
                        "max-age=31536000; includeSubDomains"
                    )

            await send(message)

        await self.app(
            scope,
            receive,
            send_with_security_headers,
        )
