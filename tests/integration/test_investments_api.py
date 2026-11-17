"""Integration tests for Investments, Portfolio Holdings, and Trade Execution API."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.security import create_access_token
from src.db.models import (
    AccountType,
    AssetType,
    FinancialAccount,
    InvestmentAsset,
    User,
)


def test_buy_holdings_and_sell_with_pnl(client: TestClient, db_session: Session) -> None:
    """Verify purchasing securities, inspecting weighted cost basis, and selling with P&L calculation."""
    # Seed account and asset
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Zerodha Demat",
        account_type=AccountType.INVESTMENT,
        currency="INR",
        opening_balance=Decimal("100000.00"),
    )
    asset = InvestmentAsset(
        symbol="INFY",
        name="Infosys Limited",
        asset_type=AssetType.EQUITY,
        exchange="NSE",
        currency="INR",
        current_price=Decimal("1850.00"),
    )
    db_session.add_all([acc, asset])
    db_session.flush()

    # 1. Buy 10 units of INFY @ 1800 with 50 fees
    buy_payload = {
        "account_id": acc.id,
        "asset_id": asset.id,
        "quantity": "10.0000",
        "price_per_unit": "1800.00",
        "fees": "50.00",
    }
    buy_res = client.post("/api/v1/investments/buy", json=buy_payload)
    assert buy_res.status_code == 201
    holding = buy_res.json()["data"]
    assert holding["quantity"] == "10.0000"
    assert holding["total_cost"] == "18050.00"
    assert holding["cost_basis_per_unit"] == "1805.00"

    # 2. List holdings
    holdings_res = client.get("/api/v1/investments/holdings")
    assert holdings_res.status_code == 200
    holdings_list = holdings_res.json()["data"]
    assert any(h["asset_id"] == asset.id for h in holdings_list)

    # 3. Sell 5 units @ 1900 with 25 fees
    sell_payload = {
        "account_id": acc.id,
        "asset_id": asset.id,
        "quantity": "5.0000",
        "price_per_unit": "1900.00",
        "fees": "25.00",
    }
    sell_res = client.post("/api/v1/investments/sell", json=sell_payload)
    assert sell_res.status_code == 200
    pnl = sell_res.json()["data"]
    assert pnl["asset_symbol"] == "INFY"
    assert pnl["quantity_sold"] == "5.0000"
    assert pnl["gross_proceeds"] == "9500.00"
    assert pnl["net_proceeds"] == "9475.00"
    # Cost basis for 5 units = 5 * 1805.00 = 9025.00
    assert pnl["total_cost_basis"] == "9025.00"
    # Gain = 9475 - 9025 = 450.00
    assert pnl["realized_gain_loss"] == "450.00"
    assert pnl["is_gain"] is True


def test_insufficient_units_sell_rejected(client: TestClient, db_session: Session) -> None:
    """Verify attempting to sell more units than held returns validation error."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Small Trading Acc",
        account_type=AccountType.INVESTMENT,
        currency="INR",
        opening_balance=Decimal("10000.00"),
    )
    asset = InvestmentAsset(
        symbol="TCS",
        name="Tata Consultancy Services",
        asset_type=AssetType.EQUITY,
        currency="INR",
    )
    db_session.add_all([acc, asset])
    db_session.flush()

    # Buy 2 units
    client.post(
        "/api/v1/investments/buy",
        json={
            "account_id": acc.id,
            "asset_id": asset.id,
            "quantity": "2.0000",
            "price_per_unit": "3500.00",
        },
    )

    # Attempt to sell 5 units -> 422
    sell_res = client.post(
        "/api/v1/investments/sell",
        json={
            "account_id": acc.id,
            "asset_id": asset.id,
            "quantity": "5.0000",
            "price_per_unit": "3600.00",
        },
    )
    assert sell_res.status_code == 422
    assert sell_res.json()["error"]["code"] == "INSUFFICIENT_UNITS"


def test_record_dividend(client: TestClient, db_session: Session) -> None:
    """Verify recording dividend earnings on held securities."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Dividend Bank",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    asset = InvestmentAsset(
        symbol="ITC",
        name="ITC Limited",
        asset_type=AssetType.EQUITY,
        currency="INR",
    )
    db_session.add_all([acc, asset])
    db_session.flush()

    div_res = client.post(
        "/api/v1/investments/dividend",
        json={
            "account_id": acc.id,
            "asset_id": asset.id,
            "amount": "250.00",
            "notes": "Interim Dividend Q3",
        },
    )
    assert div_res.status_code == 201
    assert div_res.json()["data"]["total_amount"] == "250.00"


def test_cross_user_investment_isolation(
    unauthenticated_client: TestClient, db_session: Session
) -> None:
    """Verify user B cannot sell securities held in user A's portfolio."""
    user_a = User(id="user-inv-a", name="User A", email="inva@iso.dev")
    user_b = User(id="user-inv-b", name="User B", email="invb@iso.dev")
    acc_a = FinancialAccount(
        user_id=user_a.id,
        name="A Demat",
        account_type=AccountType.INVESTMENT,
        currency="INR",
        opening_balance=Decimal("10000.00"),
    )
    asset = InvestmentAsset(
        symbol="WIPRO",
        name="Wipro Limited",
        asset_type=AssetType.EQUITY,
        currency="INR",
    )
    db_session.add_all([user_a, user_b, acc_a, asset])
    db_session.flush()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    # User A buys stock
    unauthenticated_client.post(
        "/api/v1/investments/buy",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "account_id": acc_a.id,
            "asset_id": asset.id,
            "quantity": "10.0000",
            "price_per_unit": "450.00",
        },
    )

    # User B attempts to sell User A's stock -> 404 (account not found for user B)
    res = unauthenticated_client.post(
        "/api/v1/investments/sell",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "account_id": acc_a.id,
            "asset_id": asset.id,
            "quantity": "5.0000",
            "price_per_unit": "500.00",
        },
    )
    assert res.status_code == 404


def test_list_assets_catalog_api(
    client: TestClient, unauthenticated_client: TestClient, db_session: Session
) -> None:
    """Verify GET /api/v1/investments/assets catalog endpoint and authentication requirement."""
    # Ensure at least one test asset is present
    asset = InvestmentAsset(
        symbol="TCS",
        name="Tata Consultancy Services",
        asset_type=AssetType.EQUITY,
        exchange="NSE",
        currency="INR",
        current_price=Decimal("4100.00"),
        is_active=True,
    )
    db_session.add(asset)
    db_session.flush()

    # Unauthenticated request should fail (401)
    unauth_res = unauthenticated_client.get("/api/v1/investments/assets")
    assert unauth_res.status_code == 401

    # Authenticated request succeeds
    auth_res = client.get("/api/v1/investments/assets")
    assert auth_res.status_code == 200
    data = auth_res.json()["data"]
    assert isinstance(data, list)
    assert any(a["symbol"] == "TCS" for a in data)

    # Filter by asset_type
    filtered_res = client.get("/api/v1/investments/assets?asset_type=EQUITY")
    assert filtered_res.status_code == 200
    for a in filtered_res.json()["data"]:
        assert a["asset_type"] == "EQUITY"
