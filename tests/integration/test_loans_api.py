"""Integration tests for Loans, Fixed-Rate Amortization, and Payment Schedules API."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.security import create_access_token
from src.db.models import AccountType, FinancialAccount, User


def test_create_loan_and_record_instalment_payment(client: TestClient, db_session: Session) -> None:
    """Verify recording a loan liability, inspecting amortization schedule, and paying instalment."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Loan Servicing Account",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("50000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    loan_payload = {
        "account_id": acc.id,
        "lender_name": "HDFC Bank",
        "principal_amount": "120000.00",
        "interest_rate": "10.00",
        "interest_type": "FIXED",
        "term_months": 12,
        "start_date": "2026-01-01",
    }
    create_res = client.post("/api/v1/loans", json=loan_payload)
    assert create_res.status_code == 201
    loan_data = create_res.json()["data"]
    loan_id = loan_data["id"]
    assert loan_data["principal_amount"] == "120000.00"
    assert loan_data["term_months"] == 12
    # Verify amortization schedule was populated
    schedules = loan_data["payment_schedules"]
    assert len(schedules) == 12
    first_payment = schedules[0]
    assert first_payment["payment_number"] == 1
    assert first_payment["is_paid"] is False

    # Record payment for instalment 1
    pay_res = client.post(
        f"/api/v1/loans/{loan_id}/payment",
        json={"payment_number": 1},
    )
    assert pay_res.status_code == 200
    pay_data = pay_res.json()["data"]
    assert pay_data["is_paid"] is True
    assert pay_data["payment_number"] == 1

    # Verify updated loan details
    get_res = client.get(f"/api/v1/loans/{loan_id}")
    assert get_res.status_code == 200
    updated_loan = get_res.json()["data"]
    assert Decimal(updated_loan["remaining_balance"]) < Decimal("120000.00")


def test_list_loans(client: TestClient, db_session: Session) -> None:
    """Verify listing all loans for authenticated user."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Personal Loan Acc",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    client.post(
        "/api/v1/loans",
        json={
            "account_id": acc.id,
            "lender_name": "ICICI Bank",
            "principal_amount": "50000.00",
            "interest_rate": "12.00",
            "term_months": 6,
        },
    )

    list_res = client.get("/api/v1/loans")
    assert list_res.status_code == 200
    loans = list_res.json()["data"]
    assert isinstance(loans, list)
    assert any(loan["lender_name"] == "ICICI Bank" for loan in loans)


def test_cross_user_loan_isolation(unauthenticated_client: TestClient, db_session: Session) -> None:
    """Verify user B cannot access or record payments on user A's loan."""
    user_a = User(id="user-loan-a", name="User A", email="loana@iso.dev")
    user_b = User(id="user-loan-b", name="User B", email="loanb@iso.dev")
    acc_a = FinancialAccount(
        user_id=user_a.id,
        name="A Loan Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add_all([user_a, user_b, acc_a])
    db_session.flush()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    # User A creates loan
    loan_res = unauthenticated_client.post(
        "/api/v1/loans",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "account_id": acc_a.id,
            "lender_name": "Axis Bank",
            "principal_amount": "10000.00",
            "interest_rate": "8.00",
            "term_months": 6,
        },
    )
    loan_id = loan_res.json()["data"]["id"]

    # User B attempts to access loan -> 404
    get_res = unauthenticated_client.get(
        f"/api/v1/loans/{loan_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 404

    # User B attempts to record payment -> 404
    pay_res = unauthenticated_client.post(
        f"/api/v1/loans/{loan_id}/payment",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"payment_number": 1},
    )
    assert pay_res.status_code == 404
