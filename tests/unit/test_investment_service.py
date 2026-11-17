"""Unit tests for InvestmentService: purchases, sales, weighted cost basis, and realized P&L."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.core.exceptions import (
    InsufficientUnitsError,
)
from src.db.models.account import AccountType, FinancialAccount
from src.db.models.investment import AssetType, InvestmentAsset, InvestmentTxType
from src.db.models.user import User
from src.schemas.investment import InvestmentBuyRequest, InvestmentSellRequest
from src.services.investment_service import InvestmentService


@pytest.fixture
def investment_account(db_session: Session, sample_user: User) -> FinancialAccount:
    """Fixture providing an investment trading account."""
    acc = FinancialAccount(
        user_id=sample_user.id,
        name="Zerodha Demat",
        account_type=AccountType.INVESTMENT,
        currency="INR",
        opening_balance=Decimal("500000.00"),
    )
    db_session.add(acc)
    db_session.flush()
    return acc


@pytest.fixture
def sample_asset(db_session: Session) -> InvestmentAsset:
    """Fixture providing a stock asset."""
    asset = InvestmentAsset(
        id=str(uuid.uuid4()),
        symbol="RELIANCE",
        name="Reliance Industries Ltd",
        asset_type=AssetType.EQUITY,
        exchange="NSE",
        currency="INR",
        current_price=Decimal("2500.00"),
    )
    db_session.add(asset)
    db_session.flush()
    return asset


def test_buy_asset_first_purchase(
    db_session: Session,
    sample_user: User,
    investment_account: FinancialAccount,
    sample_asset: InvestmentAsset,
) -> None:
    """Verify first security purchase initializes holding with correct quantity and cost basis."""
    service = InvestmentService(db_session)
    payload = InvestmentBuyRequest(
        account_id=investment_account.id,
        asset_id=sample_asset.id,
        quantity=Decimal("10.0000"),
        price_per_unit=Decimal("2500.00"),
        fees=Decimal("20.00"),
        transaction_date=date(2026, 11, 1),
    )
    holding = service.buy_asset(sample_user.id, payload)
    assert holding.quantity == Decimal("10.0000")
    # Total cost = 10 * 2500 + 20 = 25020.00
    assert holding.total_cost == Decimal("25020.00")
    # Cost basis per unit = 25020 / 10 = 2502.00
    assert holding.cost_basis_per_unit == Decimal("2502.00")


def test_buy_asset_subsequent_weighted_average(
    db_session: Session,
    sample_user: User,
    investment_account: FinancialAccount,
    sample_asset: InvestmentAsset,
) -> None:
    """Verify multiple purchases recalculate weighted-average cost basis correctly."""
    service = InvestmentService(db_session)

    # 1st purchase: 10 units @ 2000 = 20,000 (0 fee)
    service.buy_asset(
        sample_user.id,
        InvestmentBuyRequest(
            account_id=investment_account.id,
            asset_id=sample_asset.id,
            quantity=Decimal("10.0000"),
            price_per_unit=Decimal("2000.00"),
            fees=Decimal("0.00"),
            transaction_date=date(2026, 11, 1),
        ),
    )

    # 2nd purchase: 10 units @ 3000 = 30,000 (0 fee)
    holding = service.buy_asset(
        sample_user.id,
        InvestmentBuyRequest(
            account_id=investment_account.id,
            asset_id=sample_asset.id,
            quantity=Decimal("10.0000"),
            price_per_unit=Decimal("3000.00"),
            fees=Decimal("0.00"),
            transaction_date=date(2026, 11, 2),
        ),
    )

    # Total quantity: 20 units
    assert holding.quantity == Decimal("20.0000")
    # Total cost: 20000 + 30000 = 50000.00
    assert holding.total_cost == Decimal("50000.00")
    # Weighted cost basis: 50000 / 20 = 2500.00
    assert holding.cost_basis_per_unit == Decimal("2500.00")


def test_sell_asset_realized_gain(
    db_session: Session,
    sample_user: User,
    investment_account: FinancialAccount,
    sample_asset: InvestmentAsset,
) -> None:
    """Verify selling security computes realized gain, net proceeds, and reduces holding."""
    service = InvestmentService(db_session)

    # Buy 10 units @ 2000 = 20000
    service.buy_asset(
        sample_user.id,
        InvestmentBuyRequest(
            account_id=investment_account.id,
            asset_id=sample_asset.id,
            quantity=Decimal("10.0000"),
            price_per_unit=Decimal("2000.00"),
            fees=Decimal("0.00"),
            transaction_date=date(2026, 11, 1),
        ),
    )

    # Sell 4 units @ 2500 with fee 10.00
    # Gross proceeds: 4 * 2500 = 10000.00
    # Net proceeds: 10000 - 10 = 9990.00
    # Cost of sold: 4 * 2000 = 8000.00
    # Realized gain: 9990 - 8000 = 1990.00
    res = service.sell_asset(
        sample_user.id,
        InvestmentSellRequest(
            account_id=investment_account.id,
            asset_id=sample_asset.id,
            quantity=Decimal("4.0000"),
            price_per_unit=Decimal("2500.00"),
            fees=Decimal("10.00"),
            transaction_date=date(2026, 11, 5),
        ),
    )

    assert res.quantity_sold == Decimal("4.0000")
    assert res.gross_proceeds == Decimal("10000.00")
    assert res.net_proceeds == Decimal("9990.00")
    assert res.total_cost_basis == Decimal("8000.00")
    assert res.realized_gain_loss == Decimal("1990.00")
    assert res.is_gain is True

    # Remaining holding: 6 units @ 2000 = 12000.00
    holdings = service.list_holdings(sample_user.id, investment_account.id)
    assert len(holdings) == 1
    assert holdings[0].quantity == Decimal("6.0000")
    assert holdings[0].cost_basis_per_unit == Decimal("2000.00")
    assert holdings[0].total_cost == Decimal("12000.00")


def test_sell_asset_insufficient_units_fails(
    db_session: Session,
    sample_user: User,
    investment_account: FinancialAccount,
    sample_asset: InvestmentAsset,
) -> None:
    """Verify attempting to sell more units than held raises InsufficientUnitsError."""
    service = InvestmentService(db_session)

    # Buy 5 units
    service.buy_asset(
        sample_user.id,
        InvestmentBuyRequest(
            account_id=investment_account.id,
            asset_id=sample_asset.id,
            quantity=Decimal("5.0000"),
            price_per_unit=Decimal("100.00"),
            fees=Decimal("0.00"),
            transaction_date=date(2026, 11, 1),
        ),
    )

    # Attempt to sell 6 units
    with pytest.raises(InsufficientUnitsError) as exc:
        service.sell_asset(
            sample_user.id,
            InvestmentSellRequest(
                account_id=investment_account.id,
                asset_id=sample_asset.id,
                quantity=Decimal("6.0000"),
                price_per_unit=Decimal("120.00"),
                transaction_date=date(2026, 11, 2),
            ),
        )
    assert "Cannot sell 6.0000 units" in exc.value.message


def test_record_dividend_success(
    db_session: Session,
    sample_user: User,
    investment_account: FinancialAccount,
    sample_asset: InvestmentAsset,
) -> None:
    """Verify recording dividend transaction."""
    service = InvestmentService(db_session)
    div_tx = service.record_dividend(
        user_id=sample_user.id,
        account_id=investment_account.id,
        asset_id=sample_asset.id,
        amount=Decimal("350.00"),
        transaction_date=date(2026, 11, 10),
        notes="Q2 Interim Dividend",
    )
    assert div_tx.id is not None
    assert div_tx.transaction_type == InvestmentTxType.DIVIDEND
    assert div_tx.total_amount == Decimal("350.00")


def test_list_assets_catalog(db_session: Session, sample_asset: InvestmentAsset) -> None:
    """Verify fetching tradeable asset catalog and filtering by asset type."""
    service = InvestmentService(db_session)

    # Add a mutual fund asset
    mf_asset = InvestmentAsset(
        id=str(uuid.uuid4()),
        symbol="NIFTYBEES",
        name="Nippon India Nifty 50 ETF",
        asset_type=AssetType.MUTUAL_FUND,
        exchange="NSE",
        currency="INR",
        current_price=Decimal("250.00"),
    )
    db_session.add(mf_asset)
    db_session.flush()

    # List all active assets
    all_assets = service.list_assets()
    symbols = [a.symbol for a in all_assets]
    assert "RELIANCE" in symbols
    assert "NIFTYBEES" in symbols

    # List with asset_type filter
    equities = service.list_assets(asset_type=AssetType.EQUITY)
    assert all(a.asset_type == AssetType.EQUITY for a in equities)
    assert "RELIANCE" in [a.symbol for a in equities]
    assert "NIFTYBEES" not in [a.symbol for a in equities]
