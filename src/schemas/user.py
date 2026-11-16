"""Pydantic schemas for User representations, authentication, and administrative management."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.db.models.user import UserRole


def validate_password_complexity(password: str) -> str:
    """Validate that candidate password satisfies cryptographic complexity constraints."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(password) > 128:
        raise ValueError("Password must not exceed 128 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        raise ValueError("Password must contain at least one special character.")
    return password


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
    confirm_password: str | None = Field(
        default=None, min_length=8, max_length=128, description="Password confirmation."
    )

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        return validate_password_complexity(v)

    @field_validator("confirm_password")
    @classmethod
    def check_passwords_match(cls, v: str | None, info: object) -> str | None:
        data = getattr(info, "data", {})
        if v is not None and "password" in data and v != data["password"]:
            raise ValueError("Passwords do not match.")
        return v


class UserLogin(BaseModel):
    """Schema for JSON login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class PasswordChangeRequest(BaseModel):
    """Schema for authenticated user password change."""

    model_config = ConfigDict(populate_by_name=True)

    old_password: str = Field(
        ...,
        min_length=1,
        alias="current_password",
        description="Current existing password.",
    )
    new_password: str = Field(..., min_length=8, max_length=128, description="New password.")
    confirm_password: str = Field(
        ..., min_length=8, max_length=128, description="Confirm new password."
    )

    @field_validator("new_password")
    @classmethod
    def check_new_password_strength(cls, v: str) -> str:
        return validate_password_complexity(v)

    @field_validator("confirm_password")
    @classmethod
    def check_new_passwords_match(cls, v: str, info: object) -> str:
        data = getattr(info, "data", {})
        if "new_password" in data and v != data["new_password"]:
            raise ValueError("New passwords do not match.")
        return v


class TokenResponse(BaseModel):
    """Standard OAuth2 Bearer token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=3600, description="Token lifetime in seconds.")
    must_change_password: bool = False
    role: str = "USER"


class UserRead(BaseModel):
    """Public user profile (strictly excludes password hashes)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str | None = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime
    updated_at: datetime


class AdminUserRead(BaseModel):
    """Administrative user record projection without financial records."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str | None = None
    role: UserRole
    is_active: bool
    must_change_password: bool
    created_at: datetime
    updated_at: datetime


class AdminUserStatusUpdate(BaseModel):
    """Schema for toggling user active/disabled status."""

    is_active: bool


class AdminResetPasswordResponse(BaseModel):
    """Schema returned when an admin initiates a temporary password reset."""

    user_id: str
    email: str
    temporary_password: str
    must_change_password: bool = True
    message: str


class AdminOverviewMetrics(BaseModel):
    """System-level operational metrics for administrator dashboard."""

    total_users: int
    active_users: int
    disabled_users: int
    recent_registrations_30d: int
    db_connected: bool
    registration_enabled: bool


class SystemSettingsRead(BaseModel):
    """Platform configuration setting."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str
    description: str | None = None
    updated_at: datetime


class SystemSettingsUpdate(BaseModel):
    """Schema for updating system settings."""

    registration_enabled: bool
