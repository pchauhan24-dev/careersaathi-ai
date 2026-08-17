from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.user import CurrentUserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get the authenticated candidate",
)
def get_authenticated_candidate(
    current_user: Annotated[User, Depends(get_current_user)],
) -> CurrentUserResponse:
    return CurrentUserResponse(
        success=True,
        message="Current user retrieved successfully.",
        data=UserResponse.model_validate(current_user),
    )
