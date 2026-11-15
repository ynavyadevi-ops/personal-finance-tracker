"""Pydantic v2 DTO schemas for Savings Goals."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class SavingsGoalCreate(BaseModel):
    """Schema for initializing a new savings milestone."""

    name: str = Field(min_length=1, max_length=100)
    target_amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    currency: str = Field(default="INR", min_length=3, max_length=3)
    target_date: date | None = None
    notes: str | None = None


class SavingsGoalRead(BaseModel):
    """Persisted savings goal representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    target_amount: Decimal
    current_amount: Decimal
    currency: str
    target_date: date | None = None
    is_achieved: bool
    notes: str | None = None
    created_at: datetime


class SavingsGoalProgress(BaseModel):
    """Calculated goal progress metrics."""

    goal_id: str
    name: str
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    progress_percentage: Decimal
    is_achieved: bool
    currency: str


class GoalContributionRequest(BaseModel):
    """Schema for adding funds to a savings goal."""

    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    notes: str | None = None


class GoalWithdrawalRequest(BaseModel):
    """Schema for withdrawing funds from a savings goal."""

    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
