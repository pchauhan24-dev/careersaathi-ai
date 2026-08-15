from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyRegisteredError
from app.db.session import get_db
from app.schemas.auth import (
    RegisterResponse,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import register_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new candidate",
)
def register_candidate(
    registration_data: UserRegister,
    session: Annotated[Session, Depends(get_db)],
) -> RegisterResponse:
    try:
        user = register_user(
            session,
            registration_data,
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return RegisterResponse(
        success=True,
        message="Account created successfully.",
        data=UserResponse.model_validate(user),
    )
