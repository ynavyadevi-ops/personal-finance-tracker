"""Pydantic schemas for FinancialAccount request and response validation."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.money import to_decimal
from src.db.models.account import AccountType


class AccountBase(BaseModel):
    """Base fields shared by account schemas."""

    name: str = Field(..., min_length=1, max_length=100, description="Account display name.")
    account_type: AccountType = Field(
        default=AccountType.CHECKING, description="Category of account."
    )
    institution_name: str | None = Field(None, max_length=100, description="Financial institution.")
    currency: str = Field(
        default="INR", min_length=3, max_length=3, description="ISO 4217 3-letter currency code."
    )
    opening_balance: Decimal = Field(
        default=Decimal("0.00"), description="Starting balance in exact Decimal."
    )

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        """Ensure currency code is uppercase."""
        return v.upper()

    @field_validator("opening_balance", mode="before")
    @classmethod
    def parse_opening_balance(cls, v: object) -> Decimal:
        """Parse monetary input to clean Decimal representation."""
        if v is None:
            return Decimal("0.00")
        if isinstance(v, str | int | float | Decimal):
            return to_decimal(v)
        raise ValueError(f"Invalid monetary value: {v}")


class AccountCreate(AccountBase):
    """Payload schema for creating a new account."""

    user_id: str | None = Field(
        None, description="Optional tenant user ID (injected from session)."
    )


class AccountUpdate(BaseModel):
    """Payload schema for modifying an existing account."""

    name: str | None = Field(None, min_length=1, max_length=100)
    account_type: AccountType | None = None
    institution_name: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class AccountRead(AccountBase):
    """Response schema representing an account."""

    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
