"""Repository layer for Investments, Assets, Holdings, and Transactions."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.investment import (
    AssetType,
    InvestmentAsset,
    InvestmentHolding,
    InvestmentTransaction,
    InvestmentTxType,
)


class InvestmentRepository:
    """Encapsulates database operations for Investment entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_asset_by_id(self, asset_id: str) -> InvestmentAsset | None:
        """Fetch asset by ID."""
        stmt = select(InvestmentAsset).where(InvestmentAsset.id == asset_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_asset_by_symbol(self, symbol: str) -> InvestmentAsset | None:
        """Fetch asset by symbol."""
        stmt = select(InvestmentAsset).where(InvestmentAsset.symbol == symbol.upper())
        return self.session.execute(stmt).scalar_one_or_none()

    def create_asset(
        self,
        symbol: str,
        name: str,
        asset_type: AssetType,
        isin: str | None = None,
        exchange: str = "NSE",
        currency: str = "INR",
        current_price: Decimal | None = None,
    ) -> InvestmentAsset:
        """Create and persist a new tradeable asset record."""
        asset = InvestmentAsset(
            symbol=symbol.upper(),
            name=name,
            asset_type=asset_type,
            isin=isin,
            exchange=exchange,
            currency=currency,
            current_price=current_price,
            is_active=True,
        )
        self.session.add(asset)
        self.session.flush()
        return asset

    def list_assets(
        self, asset_type: AssetType | None = None, active_only: bool = True
    ) -> list[InvestmentAsset]:
        """Fetch asset catalog."""
        stmt = select(InvestmentAsset)
        if active_only:
            stmt = stmt.where(InvestmentAsset.is_active.is_(True))
        if asset_type:
            stmt = stmt.where(InvestmentAsset.asset_type == asset_type)
        stmt = stmt.order_by(InvestmentAsset.symbol.asc())
        return list(self.session.execute(stmt).scalars().all())

    def get_holding(self, user_id: str, account_id: str, asset_id: str) -> InvestmentHolding | None:
        """Fetch user position in a security within an account."""
        stmt = select(InvestmentHolding).where(
            InvestmentHolding.user_id == user_id,
            InvestmentHolding.account_id == account_id,
            InvestmentHolding.asset_id == asset_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_holding(
        self,
        user_id: str,
        account_id: str,
        asset_id: str,
        quantity: Decimal,
        cost_basis_per_unit: Decimal,
        total_cost: Decimal,
        currency: str = "INR",
    ) -> InvestmentHolding:
        """Create a new holding position record."""
        holding = InvestmentHolding(
            user_id=user_id,
            account_id=account_id,
            asset_id=asset_id,
            quantity=quantity,
            cost_basis_per_unit=cost_basis_per_unit,
            total_cost=total_cost,
            currency=currency,
        )
        self.session.add(holding)
        self.session.flush()
        return holding

    def list_holdings_by_account(self, user_id: str, account_id: str) -> list[InvestmentHolding]:
        """Fetch all holdings in a specific account."""
        stmt = select(InvestmentHolding).where(
            InvestmentHolding.user_id == user_id,
            InvestmentHolding.account_id == account_id,
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_holdings_by_user(self, user_id: str) -> list[InvestmentHolding]:
        """Fetch all holdings for user across all investment accounts."""
        stmt = select(InvestmentHolding).where(InvestmentHolding.user_id == user_id)
        return list(self.session.execute(stmt).scalars().all())

    def create_transaction(
        self,
        user_id: str,
        account_id: str,
        asset_id: str,
        transaction_type: InvestmentTxType,
        transaction_date: date,
        quantity: Decimal,
        price_per_unit: Decimal,
        total_amount: Decimal,
        fees: Decimal = Decimal("0.00"),
        currency: str = "INR",
        notes: str | None = None,
        related_transaction_id: str | None = None,
    ) -> InvestmentTransaction:
        """Create and persist an investment trade ledger row."""
        inv_tx = InvestmentTransaction(
            user_id=user_id,
            account_id=account_id,
            asset_id=asset_id,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_amount=total_amount,
            fees=fees,
            currency=currency,
            notes=notes,
            related_transaction_id=related_transaction_id,
        )
        self.session.add(inv_tx)
        self.session.flush()
        return inv_tx

    def list_transactions(
        self, user_id: str, account_id: str | None = None, asset_id: str | None = None
    ) -> list[InvestmentTransaction]:
        """Query investment transaction history."""
        stmt = select(InvestmentTransaction).where(InvestmentTransaction.user_id == user_id)
        if account_id:
            stmt = stmt.where(InvestmentTransaction.account_id == account_id)
        if asset_id:
            stmt = stmt.where(InvestmentTransaction.asset_id == asset_id)
        stmt = stmt.order_by(InvestmentTransaction.transaction_date.desc())
        return list(self.session.execute(stmt).scalars().all())
