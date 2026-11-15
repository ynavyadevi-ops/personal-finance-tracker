"""Integration tests for Transactions, Transfers, Reversals, and Reconciliation API."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.security import create_access_token
from src.db.models import AccountType, FinancialAccount, User


def test_create_income_and_expense_transaction(client: TestClient, db_session: Session) -> None:
    """Verify creating income and expense transactions through REST API."""
    # Create test account
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Salary Account",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # 1. Income transaction
    income_payload = {
        "account_id": acc.id,
        "transaction_type": "INCOME",
        "amount": "50000.00",
        "description": "Monthly Salary",
        "currency": "INR",
    }
    income_res = client.post("/api/v1/transactions", json=income_payload)
    assert income_res.status_code == 201
    inc_data = income_res.json()["data"]
    assert inc_data["amount"] == "50000.00"
    assert inc_data["transaction_type"] == "INCOME"
    assert len(inc_data["entries"]) == 1
    assert inc_data["entries"][0]["entry_type"] == "DEBIT"

    # 2. Expense transaction
    expense_payload = {
        "account_id": acc.id,
        "transaction_type": "EXPENSE",
        "amount": "3500.00",
        "description": "Grocery Shopping",
        "currency": "INR",
    }
    exp_res = client.post("/api/v1/transactions", json=expense_payload)
    assert exp_res.status_code == 201
    exp_data = exp_res.json()["data"]
    assert exp_data["amount"] == "3500.00"
    assert exp_data["transaction_type"] == "EXPENSE"
    assert exp_data["entries"][0]["entry_type"] == "CREDIT"


def test_atomic_transfer_between_accounts(client: TestClient, db_session: Session) -> None:
    """Verify atomic double-entry transfer balances debits and credits."""
    acc_src = FinancialAccount(
        user_id="default-user-id",
        name="Checking Transfer",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("10000.00"),
    )
    acc_dst = FinancialAccount(
        user_id="default-user-id",
        name="Savings Transfer",
        account_type=AccountType.SAVINGS,
        currency="INR",
        opening_balance=Decimal("2000.00"),
    )
    db_session.add_all([acc_src, acc_dst])
    db_session.flush()

    transfer_payload = {
        "source_account_id": acc_src.id,
        "destination_account_id": acc_dst.id,
        "amount": "2500.00",
        "description": "Transfer to Emergency Savings",
        "currency": "INR",
    }
    res = client.post("/api/v1/transactions/transfer", json=transfer_payload)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["transaction_type"] == "TRANSFER"
    assert len(data["entries"]) == 2
    # Verify both credit and debit exist
    entry_types = {e["entry_type"] for e in data["entries"]}
    assert entry_types == {"DEBIT", "CREDIT"}


def test_transaction_reversal_creates_compensating_entries(
    client: TestClient, db_session: Session
) -> None:
    """Verify reversing a transaction generates compensating entries and audit tag."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Expense Reversal Account",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("5000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Create original expense
    orig_res = client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "transaction_type": "EXPENSE",
            "amount": "1200.00",
            "description": "Erroneous Charge",
        },
    )
    orig_id = orig_res.json()["data"]["id"]

    # Reverse
    rev_res = client.post(
        f"/api/v1/transactions/{orig_id}/reverse",
        json={"reason": "Incorrect bill amount"},
    )
    assert rev_res.status_code == 201
    rev_data = rev_res.json()["data"]
    assert rev_data["amount"] == "1200.00"
    assert "reversal_of:" in rev_data["tags"]
    # Compensating entry should be DEBIT
    assert rev_data["entries"][0]["entry_type"] == "DEBIT"


def test_account_reconciliation_endpoint(client: TestClient, db_session: Session) -> None:
    """Verify statement reconciliation calculates debits, credits, and net movement."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Reconcile Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Deposit 500
    client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "transaction_type": "INCOME",
            "amount": "500.00",
            "description": "Deposit",
        },
    )
    # Spend 200
    client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "transaction_type": "EXPENSE",
            "amount": "200.00",
            "description": "Payment",
        },
    )

    rec_res = client.get(f"/api/v1/transactions/reconcile/{acc.id}?expected_balance=1300.00")
    assert rec_res.status_code == 200
    rec = rec_res.json()["data"]
    assert rec["opening_balance"] == "1000.00"
    assert rec["total_debits"] == "500.00"
    assert rec["total_credits"] == "200.00"
    assert rec["current_balance"] == "1300.00"
    assert rec["is_reconciled"] is True
    assert rec["discrepancy"] == "0.00"


def test_cross_user_transaction_isolation(
    unauthenticated_client: TestClient, db_session: Session
) -> None:
    """Verify user B cannot access or reverse transactions created by user A."""
    user_a = User(id="user-isolation-a", name="User A", email="a@iso.dev")
    user_b = User(id="user-isolation-b", name="User B", email="b@iso.dev")
    acc_a = FinancialAccount(
        user_id=user_a.id,
        name="A Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("100.00"),
    )
    db_session.add_all([user_a, user_b, acc_a])
    db_session.flush()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    # User A creates transaction
    tx_res = unauthenticated_client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "account_id": acc_a.id,
            "transaction_type": "INCOME",
            "amount": "100.00",
            "description": "Secret Income",
        },
    )
    tx_id = tx_res.json()["data"]["id"]

    # User B attempts to access it -> 404
    get_res = unauthenticated_client.get(
        f"/api/v1/transactions/{tx_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 404

    # User B attempts to reverse it -> 404
    rev_res = unauthenticated_client.post(
        f"/api/v1/transactions/{tx_id}/reverse",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"reason": "Malicious Reversal"},
    )
    assert rev_res.status_code == 404
