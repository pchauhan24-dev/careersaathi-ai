from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class UserRegister(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=120,
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized_name = " ".join(value.split())

        if len(normalized_name) < 2:
            raise ValueError("Full name must contain at least two characters.")

        return normalized_name

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class GoogleLoginRequest(BaseModel):
    credential: str = Field(
        min_length=100,
        max_length=4096,
    )


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccessTokenData(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse


class RegisterResponse(BaseModel):
    success: bool
    message: str
    data: UserResponse


class LoginResponse(BaseModel):
    success: bool
    message: str
    data: AccessTokenData


class LogoutResponse(BaseModel):
    success: bool
    message: str


class EmailVerificationRequest(BaseModel):
    token: str = Field(
        min_length=32,
        max_length=512,
    )


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        min_length=32,
        max_length=512,
    )
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )


class ResendEmailVerificationRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class EmailVerificationResponse(BaseModel):
    success: bool
    message: str
    data: UserResponse


class MessageResponse(BaseModel):
    success: bool
    message: str
