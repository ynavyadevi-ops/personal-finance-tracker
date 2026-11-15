"""Pydantic v2 DTO schemas for Transactions and double-entry Ledger operations."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.account import AccountType
from src.db.models.transaction import EntryType, TransactionType


class TransactionEntryCreate(BaseModel):
    """Schema for individual ledger line item creation."""

    account_id: str
    category_id: str | None = None
    entry_type: EntryType
    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    currency: str = Field(default="INR", min_length=3, max_length=3)
    notes: str | None = None


class TransactionEntryRead(BaseModel):
    """Schema representing persisted ledger entry."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    transaction_id: str
    account_id: str
    category_id: str | None = None
    entry_type: EntryType
    amount: Decimal
    currency: str
    notes: str | None = None
    created_at: datetime


class TransactionCreate(BaseModel):
    """Schema for creating a standard income or expense transaction."""

    account_id: str
    category_id: str | None = None
    transaction_type: TransactionType = TransactionType.EXPENSE
    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    description: str = Field(min_length=1, max_length=255)
    transaction_date: date = Field(default_factory=date.today)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    notes: str | None = None
    tags: str | None = None
    idempotency_key: str | None = None


class TransferCreate(BaseModel):
    """Schema for transferring funds between two user accounts."""

    source_account_id: str
    destination_account_id: str
    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    currency: str = Field(default="INR", min_length=3, max_length=3)
    description: str = Field(default="Account Transfer", min_length=1, max_length=255)
    transaction_date: date = Field(default_factory=date.today)
    notes: str | None = None
    tags: str | None = None
    idempotency_key: str | None = None


class TransactionRead(BaseModel):
    """Schema representing fully persisted transaction with child entries."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    transaction_date: date
    transaction_type: TransactionType
    description: str
    amount: Decimal
    currency: str
    notes: str | None = None
    tags: str | None = None
    recurring_rule_id: str | None = None
    entries: list[TransactionEntryRead] = []
    created_at: datetime


class AccountReconciliation(BaseModel):
    """Detailed reconciliation breakdown verifying account balance integrity."""

    account_id: str
    account_name: str
    account_type: AccountType
    currency: str
    opening_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
    net_movement: Decimal
    current_balance: Decimal
    posted_entry_count: int
    expected_balance: Decimal | None = None
    discrepancy: Decimal = Decimal("0.00")
    is_reconciled: bool = True
