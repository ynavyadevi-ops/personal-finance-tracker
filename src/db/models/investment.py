"""SQLAlchemy models for Investments: Assets, Holdings, and Investment Transactions."""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
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


class AssetType(str, enum.Enum):
    """Investment asset classes."""

    EQUITY = "EQUITY"
    MUTUAL_FUND = "MUTUAL_FUND"
    ETF = "ETF"
    BOND = "BOND"
    GOLD = "GOLD"
    CRYPTO = "CRYPTO"
    OTHER = "OTHER"


class InvestmentTxType(str, enum.Enum):
    """Types of investment portfolio operations."""

    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    INTEREST = "INTEREST"


class InvestmentAsset(Base, TimestampMixin):
    """Security or tradeable asset master record."""

    __tablename__ = "investment_assets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    symbol: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    asset_type: Mapped[AssetType] = mapped_column(
        SQLEnum(AssetType, native_enum=False),
        nullable=False,
        default=AssetType.EQUITY,
        index=True,
    )
    isin: Mapped[str | None] = mapped_column(
        String(12),
        unique=True,
        nullable=True,
        index=True,
    )
    exchange: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default="NSE",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )
    current_price: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    last_price_update: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Relationships
    holdings: Mapped[list["InvestmentHolding"]] = relationship(
        back_populates="asset",
    )
    transactions: Mapped[list["InvestmentTransaction"]] = relationship(
        back_populates="asset",
    )

    def __repr__(self) -> str:
        return (
            f"<InvestmentAsset(symbol='{self.symbol}', name='{self.name}', type={self.asset_type})>"
        )


class InvestmentHolding(Base, TimestampMixin):
    """User position in an asset within a designated investment account."""

    __tablename__ = "investment_holdings"

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
    asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investment_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    cost_basis_per_unit: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    current_value: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="holdings",
    )
    account: Mapped["FinancialAccount"] = relationship(
        back_populates="investment_holdings",
    )
    asset: Mapped["InvestmentAsset"] = relationship(
        back_populates="holdings",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "account_id", "asset_id", name="uq_holdings_user_acc_asset"),
        CheckConstraint("quantity >= 0", name="chk_holdings_non_negative_qty"),
        CheckConstraint("cost_basis_per_unit >= 0", name="chk_holdings_non_negative_cost_basis"),
        CheckConstraint("total_cost >= 0", name="chk_holdings_non_negative_total_cost"),
    )

    def __repr__(self) -> str:
        return (
            f"<InvestmentHolding(id={self.id}, qty={self.quantity}, total_cost={self.total_cost})>"
        )


class InvestmentTransaction(Base, TimestampMixin):
    """Historical ledger of investment buy, sell, and income events."""

    __tablename__ = "investment_transactions"

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
    asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investment_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[InvestmentTxType] = mapped_column(
        SQLEnum(InvestmentTxType, native_enum=False),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
    )
    price_per_unit: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    fees: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
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
    related_transaction_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="investment_transactions",
    )
    account: Mapped["FinancialAccount"] = relationship(
        back_populates="investment_transactions",
    )
    asset: Mapped["InvestmentAsset"] = relationship(
        back_populates="transactions",
        lazy="selectin",
    )
    related_transaction: Mapped["Transaction | None"] = relationship()

    __table_args__ = (
        Index("ix_inv_tx_user_date", "user_id", "transaction_date"),
        CheckConstraint("quantity >= 0", name="chk_inv_tx_non_negative_qty"),
        CheckConstraint("price_per_unit >= 0", name="chk_inv_tx_non_negative_price"),
        CheckConstraint("total_amount >= 0", name="chk_inv_tx_non_negative_amount"),
        CheckConstraint("fees >= 0", name="chk_inv_tx_non_negative_fees"),
    )

    def __repr__(self) -> str:
        return f"<InvestmentTransaction(id={self.id}, type={self.transaction_type}, total={self.total_amount})>"
