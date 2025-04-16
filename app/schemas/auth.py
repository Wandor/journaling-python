from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from typing import Annotated
from uuid import UUID

class LoginSchema(BaseModel):
    emailAddress: EmailStr
    password: str = Field(min_length=8)

    @field_validator("emailAddress", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class RefreshTokenSchema(BaseModel):
    userId: Annotated[UUID, Field(alias="userId")]
    refreshToken: str = Field(min_length=8)

    class Config:
        populate_by_name = True


class VerifyOTPSchema(BaseModel):
    userId: Annotated[UUID, Field(alias="userId")]
    otpValue: str = Field(min_length=6)

    class Config:
        populate_by_name = True


class UserIdSchema(BaseModel):
    userId: Annotated[UUID, Field(alias="userId")]

    class Config:
        populate_by_name = True


class ResetPasswordSchema(BaseModel):
    emailAddress: EmailStr
    password: str = Field(min_length=8)

    @field_validator("emailAddress", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class AuthenticatedUser(BaseModel):
    user_id: UUID
    role: str

    class Config:
        from_attributes = True