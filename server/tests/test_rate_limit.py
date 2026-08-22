from uuid import uuid4

import pytest
from fastapi import HTTPException, Request, status
from limits import parse

from app.core.config import settings
from app.core.rate_limit import (
    RATE_LIMIT_ERROR_DETAIL,
    RateLimitManager,
    create_rate_limit_dependency,
    get_client_identifier,
)


def create_request(
    client_host: str = "203.0.113.10",
) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [],
            "client": (client_host, 50000),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )


def test_rate_limit_manager_rejects_excess_requests() -> None:
    manager = RateLimitManager("memory://")
    rate_limit = parse("2/minute")
    scope = f"test-{uuid4()}"

    manager.enforce(
        rate_limit,
        scope,
        "203.0.113.10",
    )
    manager.enforce(
        rate_limit,
        scope,
        "203.0.113.10",
    )

    with pytest.raises(HTTPException) as exception_information:
        manager.enforce(
            rate_limit,
            scope,
            "203.0.113.10",
        )

    exception = exception_information.value

    assert exception.status_code == (status.HTTP_429_TOO_MANY_REQUESTS)
    assert exception.detail == RATE_LIMIT_ERROR_DETAIL
    assert exception.headers is not None
    assert int(exception.headers["Retry-After"]) >= 1


def test_rate_limit_buckets_are_isolated_by_client() -> None:
    manager = RateLimitManager("memory://")
    rate_limit = parse("1/minute")
    scope = f"test-{uuid4()}"

    manager.enforce(
        rate_limit,
        scope,
        "203.0.113.10",
    )

    manager.enforce(
        rate_limit,
        scope,
        "203.0.113.11",
    )


def test_get_client_identifier_uses_connection_address() -> None:
    request = create_request("198.51.100.25")

    assert get_client_identifier(request) == "198.51.100.25"


def test_rate_limit_dependency_can_be_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependency = create_rate_limit_dependency(
        "1/minute",
        f"test-{uuid4()}",
    )
    request = create_request()

    monkeypatch.setattr(
        settings,
        "rate_limit_enabled",
        False,
    )

    dependency(request)
    dependency(request)
