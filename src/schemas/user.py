"""Pydantic schemas for User representations and authentication."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user attributes."""

    name: str = Field(..., min_length=1, max_length=100)
    email: str | None = Field(
        None,
        max_length=255,
        description="User email address.",
    )


class UserCreate(UserBase):
    """Schema for internal user provisioning."""

    pass


class UserRegister(BaseModel):
    """Schema for new user registration with secure password."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(
        ..., min_length=8, max_length=128, description="Plaintext candidate password."
    )


class UserLogin(BaseModel):
    """Schema for JSON login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Standard OAuth2 Bearer token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=3600, description="Token lifetime in seconds.")


class UserRead(BaseModel):
    """Public user profile (strictly excludes password hashes)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str | None = None
    created_at: datetime
    updated_at: datetime
