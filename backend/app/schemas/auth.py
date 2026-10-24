from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    display_name: Optional[str] = Field(None, max_length=100)

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9_]{3,50}$", v):
            raise ValueError("Username must be 3-50 chars: lowercase letters, numbers, underscore")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = re.sub(r"\s+", "", v)
        if not re.match(r"^\+?254[17]\d{8}$|^0[17]\d{8}$", v):
            raise ValueError("Phone must be a valid Kenyan number")
        return v


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    phone_verified: bool
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    message: str
