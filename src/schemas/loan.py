"""Pydantic v2 DTO schemas for Loans, Debts, and Payment Schedules."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.loan import InterestType


class LoanCreate(BaseModel):
    """Schema for recording a new loan liability obligation."""

    account_id: str
    lender_name: str = Field(min_length=1, max_length=100)
    principal_amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    interest_rate: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)]
    interest_type: InterestType = InterestType.FIXED
    term_months: Annotated[int, Field(gt=0, le=600)]
    start_date: date = Field(default_factory=date.today)
    due_date: date | None = None
    notes: str | None = None


class LoanPaymentScheduleRead(BaseModel):
    """Persisted amortization schedule instalment."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    loan_id: str
    payment_number: int
    due_date: date
    principal_component: Decimal
    interest_component: Decimal
    total_payment: Decimal
    remaining_balance: Decimal
    is_paid: bool
    paid_date: date | None = None
    transaction_id: str | None = None


class LoanRead(BaseModel):
    """Persisted loan liability representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    account_id: str
    lender_name: str
    principal_amount: Decimal
    remaining_balance: Decimal
    interest_rate: Decimal
    interest_type: InterestType
    term_months: int
    minimum_monthly_payment: Decimal
    start_date: date
    due_date: date | None = None
    is_settled: bool
    notes: str | None = None
    payment_schedules: list[LoanPaymentScheduleRead] = []
    created_at: datetime


class AmortizationScheduleItem(BaseModel):
    """Calculated single instalment in an amortization breakdown."""

    payment_number: int
    due_date: date
    principal_component: Decimal
    interest_component: Decimal
    total_payment: Decimal
    remaining_balance: Decimal


class LoanPaymentRequest(BaseModel):
    """Schema for recording a loan instalment payment."""

    payment_number: Annotated[int, Field(gt=0)]
    transaction_id: str | None = None
