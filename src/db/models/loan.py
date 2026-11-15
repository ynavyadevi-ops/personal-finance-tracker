"""SQLAlchemy models for Loans, Debts, and Payment Amortization Schedules."""

import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from src.db.models.account import FinancialAccount
    from src.db.models.transaction import Transaction
    from src.db.models.user import User


class InterestType(str, enum.Enum):
    """Interest rate computation models."""

    FIXED = "FIXED"
    FLOATING = "FLOATING"


class LoanDebt(Base, TimestampMixin):
    """LoanDebt entity tracking liability obligations and interest details."""

    __tablename__ = "loan_debts"

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
    lender_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    remaining_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    interest_type: Mapped[InterestType] = mapped_column(
        SQLEnum(InterestType, native_enum=False),
        nullable=False,
        default=InterestType.FIXED,
    )
    term_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    minimum_monthly_payment: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_settled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="loans",
    )
    account: Mapped["FinancialAccount"] = relationship(
        back_populates="loans",
    )
    payment_schedules: Mapped[list["LoanPaymentSchedule"]] = relationship(
        back_populates="loan",
        cascade="all, delete-orphan",
        order_by="LoanPaymentSchedule.payment_number",
    )

    __table_args__ = (
        Index("ix_loan_debts_user_settled", "user_id", "is_settled"),
        CheckConstraint("principal_amount > 0", name="chk_loan_debts_positive_principal"),
        CheckConstraint("remaining_balance >= 0", name="chk_loan_debts_non_negative_remaining"),
        CheckConstraint("interest_rate >= 0", name="chk_loan_debts_non_negative_interest"),
        CheckConstraint("term_months > 0", name="chk_loan_debts_positive_term"),
    )

    def __repr__(self) -> str:
        return f"<LoanDebt(id={self.id}, lender='{self.lender_name}', remaining={self.remaining_balance}/{self.principal_amount})>"


class LoanPaymentSchedule(Base, TimestampMixin):
    """Amortization payment schedule instalment for a loan."""

    __tablename__ = "loan_payment_schedules"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    loan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("loan_debts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    principal_component: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    interest_component: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    total_payment: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    remaining_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    is_paid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    paid_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    transaction_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    loan: Mapped["LoanDebt"] = relationship(
        back_populates="payment_schedules",
    )
    transaction: Mapped["Transaction | None"] = relationship()

    __table_args__ = (
        UniqueConstraint("loan_id", "payment_number", name="uq_loan_schedules_loan_number"),
        CheckConstraint("payment_number > 0", name="chk_loan_schedules_positive_number"),
        CheckConstraint("total_payment > 0", name="chk_loan_schedules_positive_total"),
    )

    def __repr__(self) -> str:
        return f"<LoanPaymentSchedule(loan_id={self.loan_id}, instalment #{self.payment_number}: {self.total_payment}, paid={self.is_paid})>"
