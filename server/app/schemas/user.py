from pydantic import BaseModel

from app.schemas.auth import UserResponse


class CurrentUserResponse(BaseModel):
    success: bool
    message: str
    data: UserResponse
