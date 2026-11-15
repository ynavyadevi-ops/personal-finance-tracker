"""Pydantic v2 DTO schemas for Budgets and Category Utilization."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    """Schema for establishing a monthly category budget."""

    category_id: str
    month: Annotated[int, Field(ge=1, le=12)]
    year: Annotated[int, Field(ge=2000, le=2100)]
    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    rollover_enabled: bool = False
    notes: str | None = None


class BudgetRead(BaseModel):
    """Persisted budget representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    category_id: str
    month: int
    year: int
    amount: Decimal
    rollover_enabled: bool
    notes: str | None = None
    created_at: datetime


class BudgetUtilization(BaseModel):
    """Calculated category budget consumption and threshold metrics."""

    budget_id: str
    category_id: str
    category_name: str
    month: int
    year: int
    budgeted_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    utilization_percentage: Decimal
    is_overspent: bool
    status: str  # NORMAL (<80%), WARNING (80-99.99%), EXCEEDED (>=100%)
    rollover_amount: Decimal = Decimal("0.00")
