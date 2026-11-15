"""Pydantic v2 DTO schemas for Investments, Holdings, and Trades."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.investment import AssetType, InvestmentTxType


class InvestmentBuyRequest(BaseModel):
    """Schema for purchasing an investment security."""

    account_id: str
    asset_id: str
    quantity: Annotated[Decimal, Field(gt=Decimal("0.0000"), decimal_places=4)]
    price_per_unit: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    fees: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)] = Decimal("0.00")
    transaction_date: date = Field(default_factory=date.today)
    notes: str | None = None


class InvestmentSellRequest(BaseModel):
    """Schema for liquidating an investment security."""

    account_id: str
    asset_id: str
    quantity: Annotated[Decimal, Field(gt=Decimal("0.0000"), decimal_places=4)]
    price_per_unit: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    fees: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)] = Decimal("0.00")
    transaction_date: date = Field(default_factory=date.today)
    notes: str | None = None


class InvestmentAssetRead(BaseModel):
    """Persisted asset master entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    symbol: str
    name: str
    asset_type: AssetType
    isin: str | None = None
    exchange: str | None = None
    currency: str
    current_price: Decimal | None = None
    is_active: bool


class InvestmentHoldingRead(BaseModel):
    """Persisted holding position representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    account_id: str
    asset_id: str
    quantity: Decimal
    cost_basis_per_unit: Decimal
    total_cost: Decimal
    current_value: Decimal | None = None
    currency: str
    asset: InvestmentAssetRead | None = None


class InvestmentTransactionRead(BaseModel):
    """Persisted investment transaction event."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    account_id: str
    asset_id: str
    transaction_type: InvestmentTxType
    transaction_date: date
    quantity: Decimal
    price_per_unit: Decimal
    total_amount: Decimal
    fees: Decimal
    currency: str
    notes: str | None = None
    created_at: datetime


class RealizedGainLossResult(BaseModel):
    """Financial calculation result for a liquidated security position."""

    asset_symbol: str
    quantity_sold: Decimal
    price_per_unit: Decimal
    gross_proceeds: Decimal
    fees: Decimal
    net_proceeds: Decimal
    cost_basis_per_unit: Decimal
    total_cost_basis: Decimal
    realized_gain_loss: Decimal
    is_gain: bool


class DividendRequest(BaseModel):
    """Schema for recording a dividend receipt."""

    account_id: str
    asset_id: str
    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    transaction_date: date = Field(default_factory=date.today)
    notes: str | None = None
