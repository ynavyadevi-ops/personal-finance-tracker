"""SQLAlchemy models for Transactions and double-entry TransactionEntries."""

import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from src.db.models.account import FinancialAccount
    from src.db.models.category import Category
    from src.db.models.recurring import RecurringRule
    from src.db.models.user import User


class TransactionType(str, enum.Enum):
    """Business transaction classifications."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"


class EntryType(str, enum.Enum):
    """Double-entry ledger entry direction."""

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class Transaction(Base, TimestampMixin):
    """Transaction business event entity."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, native_enum=False),
        nullable=False,
        default=TransactionType.EXPENSE,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    tags: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    recurring_rule_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("recurring_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="transactions",
    )
    entries: Mapped[list["TransactionEntry"]] = relationship(
        back_populates="transaction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    recurring_rule: Mapped["RecurringRule | None"] = relationship(
        back_populates="transactions",
    )

    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_type", "user_id", "transaction_type"),
        CheckConstraint("amount > 0", name="chk_transactions_positive_amount"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, desc='{self.description}', amount={self.amount}, type={self.transaction_type})>"


class TransactionEntry(Base, TimestampMixin):
    """Individual double-entry ledger line associated with an account."""

    __tablename__ = "transaction_entries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("financial_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entry_type: Mapped[EntryType] = mapped_column(
        SQLEnum(EntryType, native_enum=False),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )
    notes: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        back_populates="entries",
    )
    account: Mapped["FinancialAccount"] = relationship(
        back_populates="transaction_entries",
    )
    category: Mapped["Category | None"] = relationship(
        back_populates="transaction_entries",
    )

    __table_args__ = (
        Index("ix_transaction_entries_account_entry", "account_id", "entry_type"),
        CheckConstraint("amount > 0", name="chk_transaction_entries_positive_amount"),
    )

    def __repr__(self) -> str:
        return f"<TransactionEntry(id={self.id}, account_id={self.account_id}, {self.entry_type}={self.amount})>"
