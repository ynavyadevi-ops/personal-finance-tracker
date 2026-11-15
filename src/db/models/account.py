"""SQLAlchemy model for Financial Accounts."""

import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from src.db.models.user import User


class AccountType(str, enum.Enum):
    """Enumeration of supported financial account categories."""

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CREDIT_CARD = "CREDIT_CARD"
    CASH = "CASH"
    INVESTMENT = "INVESTMENT"
    LOAN = "LOAN"


class FinancialAccount(Base, TimestampMixin):
    """FinancialAccount entity representing a depository, credit, or investment account."""

    __tablename__ = "financial_accounts"

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
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    account_type: Mapped[AccountType] = mapped_column(
        SQLEnum(AccountType, native_enum=False),
        nullable=False,
        default=AccountType.CHECKING,
    )
    institution_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="accounts",
    )

    __table_args__ = (
        Index("ix_financial_accounts_user_active", "user_id", "is_active"),
        Index("ix_financial_accounts_user_type", "user_id", "account_type"),
    )

    def __repr__(self) -> str:
        return f"<FinancialAccount(id={self.id}, name={self.name}, type={self.account_type}, balance={self.opening_balance})>"
