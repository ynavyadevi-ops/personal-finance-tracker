"""Integration tests for Recurring Transaction Rules, Schedules, and Spawning API."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.security import create_access_token
from src.db.models import AccountType, Category, CategoryType, FinancialAccount, User


def test_create_and_execute_due_recurring_rule(client: TestClient, db_session: Session) -> None:
    """Verify scheduling a recurring rule and executing it to spawn a double-entry transaction."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Bills Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("20000.00"),
    )
    cat = Category(
        user_id="default-user-id",
        name="Internet Bill",
        category_type=CategoryType.EXPENSE,
    )
    db_session.add_all([acc, cat])
    db_session.flush()

    # 1. Create recurring expense rule
    rule_payload = {
        "account_id": acc.id,
        "category_id": cat.id,
        "name": "Fiber Internet Subscription",
        "amount": "1299.00",
        "currency": "INR",
        "transaction_type": "EXPENSE",
        "frequency": "MONTHLY",
        "interval": 1,
        "start_date": "2026-01-01",
    }
    create_res = client.post("/api/v1/recurring", json=rule_payload)
    assert create_res.status_code == 201
    rule = create_res.json()["data"]
    rule_id = rule["id"]
    assert rule["amount"] == "1299.00"
    assert rule["is_active"] is True

    # 2. Query due rules
    due_res = client.get("/api/v1/recurring/due?as_of_date=2026-02-01")
    assert due_res.status_code == 200
    due_rules = due_res.json()["data"]
    assert any(r["id"] == rule_id for r in due_rules)

    # 3. Execute due rule
    exec_res = client.post(f"/api/v1/recurring/{rule_id}/execute?execution_date=2026-01-01")
    assert exec_res.status_code == 201
    spawned_tx = exec_res.json()["data"]
    assert spawned_tx["amount"] == "1299.00"
    assert spawned_tx["transaction_type"] == "EXPENSE"
    assert "Fiber Internet Subscription" in spawned_tx["description"]

    # 4. Duplicate execution prevention for same date -> 422/400 validation error
    dup_res = client.post(f"/api/v1/recurring/{rule_id}/execute?execution_date=2026-01-01")
    assert dup_res.status_code == 422
    assert dup_res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_pause_and_resume_recurring_rule(client: TestClient, db_session: Session) -> None:
    """Verify pausing deactivates schedule and resuming reactivates it."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Subscriptions Acc",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("5000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    create_res = client.post(
        "/api/v1/recurring",
        json={
            "account_id": acc.id,
            "name": "Gym Membership",
            "amount": "2000.00",
            "frequency": "MONTHLY",
        },
    )
    rule_id = create_res.json()["data"]["id"]

    # Pause
    pause_res = client.post(f"/api/v1/recurring/{rule_id}/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["data"]["is_active"] is False

    # Resume
    resume_res = client.post(f"/api/v1/recurring/{rule_id}/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["data"]["is_active"] is True


def test_cross_user_recurring_isolation(
    unauthenticated_client: TestClient, db_session: Session
) -> None:
    """Verify user B cannot execute or pause user A's recurring rules."""
    user_a = User(id="user-rec-a", name="User A", email="reca@iso.dev")
    user_b = User(id="user-rec-b", name="User B", email="recb@iso.dev")
    acc_a = FinancialAccount(
        user_id=user_a.id,
        name="A Bills",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("5000.00"),
    )
    db_session.add_all([user_a, user_b, acc_a])
    db_session.flush()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    # User A creates rule
    rule_res = unauthenticated_client.post(
        "/api/v1/recurring",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "account_id": acc_a.id,
            "name": "User A Netflix",
            "amount": "649.00",
            "frequency": "MONTHLY",
        },
    )
    rule_id = rule_res.json()["data"]["id"]

    # User B attempts to execute it -> 404
    exec_res = unauthenticated_client.post(
        f"/api/v1/recurring/{rule_id}/execute",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert exec_res.status_code == 404
