"""Integration tests for Budgets and Category Utilization API."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.security import create_access_token
from src.db.models import AccountType, Category, CategoryType, FinancialAccount, User


def test_set_budget_and_fetch_utilization(client: TestClient, db_session: Session) -> None:
    """Verify setting monthly budget allocation and computing spending utilization."""
    cat = Category(
        user_id="default-user-id",
        name="Dining Out",
        category_type=CategoryType.EXPENSE,
    )
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Dining Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("10000.00"),
    )
    db_session.add_all([cat, acc])
    db_session.flush()

    # Set budget for 2026-11
    budget_payload = {
        "category_id": cat.id,
        "month": 11,
        "year": 2026,
        "amount": "10000.00",
        "rollover_enabled": False,
    }
    set_res = client.post("/api/v1/budgets", json=budget_payload)
    assert set_res.status_code == 201
    assert set_res.json()["data"]["amount"] == "10000.00"

    # Spend 8500 in Dining Out
    client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "category_id": cat.id,
            "transaction_type": "EXPENSE",
            "amount": "8500.00",
            "description": "Dinner at Taj",
            "transaction_date": "2026-11-15",
        },
    )

    # Fetch utilization
    util_res = client.get(f"/api/v1/budgets/utilization?category_id={cat.id}&month=11&year=2026")
    assert util_res.status_code == 200
    util = util_res.json()["data"]
    assert util["budgeted_amount"] == "10000.00"
    assert util["spent_amount"] == "8500.00"
    assert util["remaining_amount"] == "1500.00"
    assert util["utilization_percentage"] == "85.00"
    assert util["status"] == "WARNING"  # 80-99.99% threshold


def test_list_period_budgets(client: TestClient, db_session: Session) -> None:
    """Verify listing all configured budget utilizations for a period."""
    cat = Category(
        user_id="default-user-id",
        name="Entertainment Period",
        category_type=CategoryType.EXPENSE,
    )
    db_session.add(cat)
    db_session.flush()

    client.post(
        "/api/v1/budgets",
        json={
            "category_id": cat.id,
            "month": 11,
            "year": 2026,
            "amount": "5000.00",
        },
    )

    list_res = client.get("/api/v1/budgets/period?month=11&year=2026")
    assert list_res.status_code == 200
    items = list_res.json()["data"]
    assert isinstance(items, list)
    assert any(b["category_id"] == cat.id for b in items)


def test_cross_user_budget_isolation(
    unauthenticated_client: TestClient, db_session: Session
) -> None:
    """Verify user B cannot set a budget on a category owned by user A."""
    user_a = User(id="user-cat-a", name="User A", email="cata@iso.dev")
    user_b = User(id="user-cat-b", name="User B", email="catb@iso.dev")
    cat_a = Category(
        user_id=user_a.id, name="User A Private Cat", category_type=CategoryType.EXPENSE
    )
    db_session.add_all([user_a, user_b, cat_a])
    db_session.flush()

    token_b = create_access_token(user_b.id)

    # User B attempts to set budget on user A's category -> 404
    res = unauthenticated_client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "category_id": cat_a.id,
            "month": 11,
            "year": 2026,
            "amount": "1000.00",
        },
    )
    assert res.status_code == 404
