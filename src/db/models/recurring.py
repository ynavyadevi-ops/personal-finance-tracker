"""SQLAlchemy model for Recurring Transaction Rules."""

import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, generate_uuid
from src.db.models.transaction import TransactionType

if TYPE_CHECKING:
    from src.db.models.account import FinancialAccount
    from src.db.models.category import Category
    from src.db.models.transaction import Transaction
    from src.db.models.user import User


class Frequency(str, enum.Enum):
    """Recurrence intervals for scheduled rules."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class RecurringRule(Base, TimestampMixin):
    """RecurringRule entity defining templates for automated bills and earnings."""

    __tablename__ = "recurring_rules"

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
    destination_account_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("financial_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
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
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, native_enum=False),
        nullable=False,
        default=TransactionType.EXPENSE,
    )
    frequency: Mapped[Frequency] = mapped_column(
        SQLEnum(Frequency, native_enum=False),
        nullable=False,
        default=Frequency.MONTHLY,
    )
    interval: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    next_occurrence: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="recurring_rules",
    )
    account: Mapped["FinancialAccount"] = relationship(
        "FinancialAccount",
        foreign_keys=[account_id],
        back_populates="recurring_rules",
    )
    destination_account: Mapped["FinancialAccount | None"] = relationship(
        "FinancialAccount",
        foreign_keys=[destination_account_id],
    )
    category: Mapped["Category | None"] = relationship()
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="recurring_rule",
    )

    __table_args__ = (
        Index("ix_recurring_rules_active_next", "is_active", "next_occurrence"),
        CheckConstraint("amount > 0", name="chk_recurring_rules_positive_amount"),
        CheckConstraint('"interval" > 0', name="chk_recurring_rules_positive_interval"),
    )

    def __repr__(self) -> str:
        return f"<RecurringRule(id={self.id}, name='{self.name}', amount={self.amount}, freq={self.frequency})>"
