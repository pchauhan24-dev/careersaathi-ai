from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import check_database_connection
from app.schemas.health import (
    DatabaseHealthData,
    DatabaseHealthResponse,
    HealthData,
    HealthResponse,
)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API health",
)
def get_health() -> HealthResponse:
    return HealthResponse(
        success=True,
        message="CareerSaathi AI API is running.",
        data=HealthData(
            status="healthy",
            environment=settings.environment,
            version=settings.app_version,
        ),
    )


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    summary="Check database connection",
)
def get_database_health() -> DatabaseHealthResponse:
    try:
        check_database_connection()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL database connection is unavailable.",
        ) from exc

    return DatabaseHealthResponse(
        success=True,
        message="PostgreSQL database connection is working.",
        data=DatabaseHealthData(status="connected"),
    )
