from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware,
)

from app.api.router import api_router
from app.core.config import settings
from app.middleware.security_headers import (
    SecurityHeadersMiddleware,
)

ALLOWED_CORS_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

ALLOWED_CORS_HEADERS = [
    "Accept",
    "Authorization",
    "Content-Type",
    "X-Requested-With",
]

EXPOSED_CORS_HEADERS = [
    "Retry-After",
]


def create_app() -> FastAPI:
    documentation_url = "/docs" if settings.api_docs_enabled else None
    openapi_url = "/openapi.json" if settings.api_docs_enabled else None
    redoc_url = "/redoc" if settings.api_docs_enabled else None

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend API for résumé intelligence, job matching, and AI mock interviews."
        ),
        docs_url=documentation_url,
        openapi_url=openapi_url,
        redoc_url=redoc_url,
    )

    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_host_list,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.client_url],
        allow_credentials=True,
        allow_methods=ALLOWED_CORS_METHODS,
        allow_headers=ALLOWED_CORS_HEADERS,
        expose_headers=EXPOSED_CORS_HEADERS,
    )

    application.add_middleware(
        SecurityHeadersMiddleware,
        environment=settings.environment,
        sensitive_path_prefixes=(
            f"{settings.api_v1_prefix}/auth",
            f"{settings.api_v1_prefix}/users",
        ),
    )

    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    return application


app = create_app()
