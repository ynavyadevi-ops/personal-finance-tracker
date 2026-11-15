"""SQLAlchemy model for Users."""

from typing import TYPE_CHECKING

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from src.db.models.account import FinancialAccount
    from src.db.models.audit import AuditLog
    from src.db.models.budget import Budget
    from src.db.models.category import Category
    from src.db.models.goal import SavingsGoal
    from src.db.models.investment import InvestmentHolding, InvestmentTransaction
    from src.db.models.loan import LoanDebt
    from src.db.models.recurring import RecurringRule
    from src.db.models.transaction import Transaction


class User(Base, TimestampMixin):
    """User entity representing an account owner."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    accounts: Mapped[list["FinancialAccount"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    savings_goals: Mapped[list["SavingsGoal"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    loans: Mapped[list["LoanDebt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recurring_rules: Mapped[list["RecurringRule"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    holdings: Mapped[list["InvestmentHolding"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    investment_transactions: Mapped[list["InvestmentTransaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_users_name", "name"),)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name})>"
