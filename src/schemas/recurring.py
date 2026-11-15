"""Pydantic v2 DTO schemas for Recurring Transaction Rules."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.db.models.recurring import Frequency
from src.db.models.transaction import TransactionType


class RecurringRuleCreate(BaseModel):
    """Schema for scheduling automated recurring templates."""

    account_id: str
    name: str = Field(min_length=1, max_length=100)
    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    currency: str = Field(default="INR", min_length=3, max_length=3)
    transaction_type: TransactionType = TransactionType.EXPENSE
    frequency: Frequency = Frequency.MONTHLY
    interval: Annotated[int, Field(gt=0, le=365)] = 1
    start_date: date = Field(default_factory=date.today)
    end_date: date | None = None
    category_id: str | None = None
    destination_account_id: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "RecurringRuleCreate":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("Recurring rule end date cannot be earlier than start date.")
        return self


class RecurringRuleRead(BaseModel):
    """Persisted recurring rule representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    account_id: str
    category_id: str | None = None
    destination_account_id: str | None = None
    name: str
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    frequency: Frequency
    interval: int
    start_date: date
    end_date: date | None = None
    next_occurrence: date
    is_active: bool
    notes: str | None = None
    created_at: datetime
