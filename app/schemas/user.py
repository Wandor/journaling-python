from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re
from datetime import datetime

class RegisterUser(BaseModel):
    userName: Optional[str] = Field(default="")
    firstName: str = Field(..., min_length=1, description="First name is required")
    lastName: str = Field(..., min_length=1, description="Last name is required")
    emailAddress: EmailStr
    mobileNumber: str
    role: str
    password: str

    @field_validator("userName", mode="before")
    @classmethod
    def trim_username(cls, v):
        return v.strip() if v else ""

    @field_validator("firstName", "lastName")
    @classmethod
    def validate_name(cls, v):
        return v.strip()

    @field_validator("mobileNumber")
    @classmethod
    def validate_mobile(cls, v):
        if not re.fullmatch(r"^\+?[1-9]\d{9,14}$", v):
            raise ValueError("Invalid mobile number format")
        if len(v) < 10 or len(v) > 15:
            raise ValueError("Mobile number must be between 10 and 15 digits")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        allowed_roles = {"USER", "ADMIN"}
        if v not in allowed_roles:
            raise ValueError("Invalid role")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserPreference(BaseModel):
    enableNotifications: bool = True
    autoTag: bool = True
    autoCategorize: bool = True
    summarize: bool = True
    reminderTime: Optional[datetime] = None
    language: str = "en"
    timeZone: str = "UTC"
    twoFactorEnabled: bool = False

    @field_validator("reminderTime")
    @classmethod
    def validate_reminder_time(cls, v):
        # Optional validation for reminderTime (if needed)
        return v

