import math
import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from limits import parse
from limits.limits import RateLimitItem
from limits.storage import storage_from_string
from limits.strategies import FixedWindowRateLimiter

from app.core.config import settings

RATE_LIMIT_ERROR_DETAIL = "Too many requests. Please try again later."


class RateLimitManager:
    def __init__(
        self,
        storage_uri: str,
    ) -> None:
        self.storage = storage_from_string(storage_uri)
        self.strategy = FixedWindowRateLimiter(self.storage)

    def enforce(
        self,
        rate_limit: RateLimitItem,
        scope: str,
        identifier: str,
    ) -> None:
        request_is_allowed = self.strategy.hit(
            rate_limit,
            scope,
            identifier,
        )

        if request_is_allowed:
            return

        window = self.strategy.get_window_stats(
            rate_limit,
            scope,
            identifier,
        )

        retry_after = max(
            1,
            math.ceil(window.reset_time - time.time()),
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=RATE_LIMIT_ERROR_DETAIL,
            headers={
                "Retry-After": str(retry_after),
            },
        )


def get_client_identifier(request: Request) -> str:
    if request.client is None:
        return "unknown"

    return request.client.host


def create_rate_limit_dependency(
    limit_value: str,
    scope: str,
) -> Callable[[Request], None]:
    rate_limit = parse(limit_value)

    def enforce_rate_limit(request: Request) -> None:
        if not settings.rate_limit_enabled or settings.environment == "test":
            return

        rate_limit_manager.enforce(
            rate_limit,
            scope,
            get_client_identifier(request),
        )

    return enforce_rate_limit


rate_limit_manager = RateLimitManager(
    settings.rate_limit_storage_uri.get_secret_value()
)
