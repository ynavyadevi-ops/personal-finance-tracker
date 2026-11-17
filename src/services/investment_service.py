"""Domain service implementing business rules for Investments, Weighted-Average Cost Basis, and Trades."""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.exceptions import (
    InsufficientUnitsError,
    NotFoundError,
    ValidationError,
)
from src.core.logging import logger
from src.core.money import to_decimal
from src.db.models.investment import AssetType, InvestmentTxType
from src.repositories.account_repo import AccountRepository
from src.repositories.investment_repo import InvestmentRepository
from src.schemas.investment import (
    InvestmentAssetRead,
    InvestmentBuyRequest,
    InvestmentHoldingRead,
    InvestmentSellRequest,
    InvestmentTransactionRead,
    RealizedGainLossResult,
)


class InvestmentService:
    """Orchestrates portfolio securities purchases, sales, weighted-average cost basis, and gain/loss math."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.investment_repo = InvestmentRepository(session)
        self.account_repo = AccountRepository(session)

    def buy_asset(self, user_id: str, payload: InvestmentBuyRequest) -> InvestmentHoldingRead:
        """Process a security purchase, updating holdings with weighted-average cost basis."""
        qty = Decimal(str(payload.quantity)).quantize(Decimal("0.0001"))
        price = to_decimal(payload.price_per_unit)
        fees = to_decimal(payload.fees)

        if qty <= Decimal("0.0000"):
            raise ValidationError("Purchased quantity must be strictly positive.")
        if price <= Decimal("0.00"):
            raise ValidationError("Purchase price per unit must be strictly positive.")
        if fees < Decimal("0.00"):
            raise ValidationError("Transaction fees cannot be negative.")

        # 1. Validate account ownership
        account = self.account_repo.get_by_id(account_id=payload.account_id, user_id=user_id)
        if not account:
            raise NotFoundError(
                f"Account with ID '{payload.account_id}' was not found for this user."
            )

        # 2. Validate asset existence
        asset = self.investment_repo.get_asset_by_id(asset_id=payload.asset_id)
        if not asset:
            raise NotFoundError(f"Investment asset with ID '{payload.asset_id}' was not found.")

        total_trade_amount = to_decimal((qty * price) + fees)

        # 3. Retrieve or create holding position
        holding = self.investment_repo.get_holding(
            user_id=user_id, account_id=payload.account_id, asset_id=payload.asset_id
        )

        if not holding:
            cost_basis = to_decimal(total_trade_amount / qty)
            holding = self.investment_repo.create_holding(
                user_id=user_id,
                account_id=payload.account_id,
                asset_id=payload.asset_id,
                quantity=qty,
                cost_basis_per_unit=cost_basis,
                total_cost=total_trade_amount,
                currency=account.currency,
            )
        else:
            # Weighted-average cost basis calculation
            new_qty = holding.quantity + qty
            new_total_cost = holding.total_cost + total_trade_amount
            new_cost_basis = to_decimal(new_total_cost / new_qty)

            holding.quantity = new_qty
            holding.total_cost = new_total_cost
            holding.cost_basis_per_unit = new_cost_basis

        # 4. Record historical investment transaction
        self.investment_repo.create_transaction(
            user_id=user_id,
            account_id=payload.account_id,
            asset_id=payload.asset_id,
            transaction_type=InvestmentTxType.BUY,
            transaction_date=payload.transaction_date,
            quantity=qty,
            price_per_unit=price,
            total_amount=total_trade_amount,
            fees=fees,
            currency=account.currency,
            notes=payload.notes,
        )

        self.session.commit()
        self.session.refresh(holding)
        logger.info(
            f"Bought {qty} of {asset.symbol} in account {account.name}. "
            f"New holding: {holding.quantity} @ ₹{holding.cost_basis_per_unit}/unit"
        )
        return InvestmentHoldingRead.model_validate(holding)

    def sell_asset(self, user_id: str, payload: InvestmentSellRequest) -> RealizedGainLossResult:
        """Process a security liquidation, enforcing holding sufficiency and calculating realized gains/losses."""
        qty = Decimal(str(payload.quantity)).quantize(Decimal("0.0001"))
        price = to_decimal(payload.price_per_unit)
        fees = to_decimal(payload.fees)

        if qty <= Decimal("0.0000"):
            raise ValidationError("Sold quantity must be strictly positive.")
        if price <= Decimal("0.00"):
            raise ValidationError("Sale price per unit must be strictly positive.")
        if fees < Decimal("0.00"):
            raise ValidationError("Transaction fees cannot be negative.")

        # 1. Validate account ownership
        account = self.account_repo.get_by_id(account_id=payload.account_id, user_id=user_id)
        if not account:
            raise NotFoundError(
                f"Account with ID '{payload.account_id}' was not found for this user."
            )

        # 2. Validate asset existence
        asset = self.investment_repo.get_asset_by_id(asset_id=payload.asset_id)
        if not asset:
            raise NotFoundError(f"Investment asset with ID '{payload.asset_id}' was not found.")

        # 3. Validate holding existence and quantity sufficiency
        holding = self.investment_repo.get_holding(
            user_id=user_id, account_id=payload.account_id, asset_id=payload.asset_id
        )
        if not holding or holding.quantity <= Decimal("0.0000"):
            raise InsufficientUnitsError(
                f"No units of {asset.symbol} are currently held in account '{account.name}'."
            )

        if qty > holding.quantity:
            raise InsufficientUnitsError(
                f"Cannot sell {qty} units of {asset.symbol}; only {holding.quantity} units are currently held."
            )

        # 4. Financial gain/loss calculations
        gross_proceeds = to_decimal(qty * price)
        net_proceeds = to_decimal(gross_proceeds - fees)
        cost_basis_per_unit = to_decimal(holding.cost_basis_per_unit)
        cost_of_sold = to_decimal(qty * cost_basis_per_unit)
        realized_gain_loss = to_decimal(net_proceeds - cost_of_sold)

        # 5. Update holding position
        new_quantity = holding.quantity - qty
        if new_quantity == Decimal("0.0000"):
            holding.quantity = Decimal("0.0000")
            holding.total_cost = Decimal("0.00")
            holding.cost_basis_per_unit = Decimal("0.00")
        else:
            holding.quantity = new_quantity
            # Maintain the weighted-average cost basis per unit for remaining shares
            holding.total_cost = to_decimal(new_quantity * cost_basis_per_unit)

        # 6. Record historical trade transaction
        self.investment_repo.create_transaction(
            user_id=user_id,
            account_id=payload.account_id,
            asset_id=payload.asset_id,
            transaction_type=InvestmentTxType.SELL,
            transaction_date=payload.transaction_date,
            quantity=qty,
            price_per_unit=price,
            total_amount=net_proceeds,
            fees=fees,
            currency=account.currency,
            notes=payload.notes,
        )

        self.session.commit()
        logger.info(
            f"Sold {qty} of {asset.symbol} in account {account.name}. "
            f"Realized P&L: ₹{realized_gain_loss} (Proceeds: ₹{net_proceeds}, Cost: ₹{cost_of_sold})"
        )

        return RealizedGainLossResult(
            asset_symbol=asset.symbol,
            quantity_sold=qty,
            price_per_unit=price,
            gross_proceeds=gross_proceeds,
            fees=fees,
            net_proceeds=net_proceeds,
            cost_basis_per_unit=cost_basis_per_unit,
            total_cost_basis=cost_of_sold,
            realized_gain_loss=realized_gain_loss,
            is_gain=realized_gain_loss >= Decimal("0.00"),
        )

    def record_dividend(
        self,
        user_id: str,
        account_id: str,
        asset_id: str,
        amount: Decimal,
        transaction_date: date | None = None,
        notes: str | None = None,
    ) -> InvestmentTransactionRead:
        """Record dividend earnings from a security position without altering share counts."""
        div_amount = to_decimal(amount)
        if div_amount <= Decimal("0.00"):
            raise ValidationError("Dividend amount must be strictly positive.")

        account = self.account_repo.get_by_id(account_id=account_id, user_id=user_id)
        if not account:
            raise NotFoundError(f"Account with ID '{account_id}' was not found.")

        asset = self.investment_repo.get_asset_by_id(asset_id=asset_id)
        if not asset:
            raise NotFoundError(f"Asset with ID '{asset_id}' was not found.")

        inv_tx = self.investment_repo.create_transaction(
            user_id=user_id,
            account_id=account_id,
            asset_id=asset_id,
            transaction_type=InvestmentTxType.DIVIDEND,
            transaction_date=transaction_date or date.today(),
            quantity=Decimal("0.0000"),
            price_per_unit=Decimal("0.00"),
            total_amount=div_amount,
            fees=Decimal("0.00"),
            currency=account.currency,
            notes=notes,
        )
        self.session.commit()
        self.session.refresh(inv_tx)
        logger.info(
            f"Recorded dividend of ₹{div_amount} from {asset.symbol} in account {account.name}"
        )
        return InvestmentTransactionRead.model_validate(inv_tx)

    def list_holdings(
        self, user_id: str, account_id: str | None = None
    ) -> list[InvestmentHoldingRead]:
        """Fetch investment positions for a user."""
        if account_id:
            holdings = self.investment_repo.list_holdings_by_account(
                user_id=user_id, account_id=account_id
            )
        else:
            holdings = self.investment_repo.list_holdings_by_user(user_id=user_id)
        return [InvestmentHoldingRead.model_validate(h) for h in holdings]

    def list_assets(
        self, asset_type: AssetType | None = None, active_only: bool = True
    ) -> list[InvestmentAssetRead]:
        """Fetch active tradeable investment securities catalog."""
        assets = self.investment_repo.list_assets(asset_type=asset_type, active_only=active_only)
        return [InvestmentAssetRead.model_validate(a) for a in assets]
