"""Phase 8 System Hardening & Comprehensive Verification Integration Tests.

Verifies financial integrity invariants, double-entry conservation, arithmetic precision,
negative/zero amount rejections, currency mismatch prevention, repeated reversal blocking,
insufficient investment unit protections, multi-tenant cross-user isolation, and backup validation.
"""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.main import app
from src.core.security import create_access_token
from src.db.models import (
    AccountType,
    Category,
    CategoryType,
    FinancialAccount,
    InvestmentAsset,
    User,
)


def create_authenticated_client(
    user_id: str, email: str, name: str, db_session: Session
) -> TestClient:
    """Helper creating a TestClient authenticated as an explicit tenant user."""
    user = db_session.get(User, user_id)
    if not user:
        user = User(id=user_id, email=email, name=name)
        db_session.add(user)
        db_session.flush()

    token = create_access_token(user_id)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


def test_zero_and_negative_amount_rejection_on_transactions(
    client: TestClient, db_session: Session
) -> None:
    """Verify transactions strictly reject zero and negative amounts with HTTP 422."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Hardening Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Zero amount
    res_zero = client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "transaction_type": "EXPENSE",
            "amount": "0.00",
            "description": "Zero expense",
        },
    )
    assert res_zero.status_code == 422

    # Negative amount
    res_neg = client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "transaction_type": "EXPENSE",
            "amount": "-50.00",
            "description": "Negative expense",
        },
    )
    assert res_neg.status_code == 422


def test_zero_and_negative_amount_rejection_on_budgets(
    client: TestClient, db_session: Session
) -> None:
    """Verify budget limits strictly reject zero and negative limits with HTTP 422."""
    cat = Category(
        user_id="default-user-id",
        name="Hardening Budget Cat",
        category_type=CategoryType.EXPENSE,
    )
    db_session.add(cat)
    db_session.flush()

    # Zero budget amount
    res_zero = client.post(
        "/api/v1/budgets",
        json={
            "category_id": cat.id,
            "month": 11,
            "year": 2026,
            "amount": "0.00",
        },
    )
    assert res_zero.status_code == 422

    # Negative budget amount
    res_neg = client.post(
        "/api/v1/budgets",
        json={
            "category_id": cat.id,
            "month": 11,
            "year": 2026,
            "amount": "-100.00",
        },
    )
    assert res_neg.status_code == 422


def test_zero_and_negative_amount_rejection_on_goals(client: TestClient) -> None:
    """Verify savings goals strictly reject zero and negative target amounts with HTTP 422."""
    res_zero = client.post(
        "/api/v1/goals",
        json={"name": "Zero Goal", "target_amount": "0.00", "currency": "INR"},
    )
    assert res_zero.status_code == 422

    res_neg = client.post(
        "/api/v1/goals",
        json={"name": "Negative Goal", "target_amount": "-500.00", "currency": "INR"},
    )
    assert res_neg.status_code == 422


def test_zero_and_negative_amount_rejection_on_loans(
    client: TestClient, db_session: Session
) -> None:
    """Verify loan principal and interest rates reject zero/negative inputs with HTTP 422."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Loan Acc",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Zero principal
    res_zero_principal = client.post(
        "/api/v1/loans",
        json={
            "account_id": acc.id,
            "lender_name": "Test Bank",
            "principal_amount": "0.00",
            "interest_rate": "8.50",
            "term_months": 12,
        },
    )
    assert res_zero_principal.status_code == 422

    # Negative interest rate
    res_neg_interest = client.post(
        "/api/v1/loans",
        json={
            "account_id": acc.id,
            "lender_name": "Test Bank",
            "principal_amount": "10000.00",
            "interest_rate": "-2.50",
            "term_months": 12,
        },
    )
    assert res_neg_interest.status_code == 422


def test_zero_and_negative_amount_rejection_on_investments(
    client: TestClient, db_session: Session
) -> None:
    """Verify investment trades reject zero/negative quantities and prices with HTTP 422."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Brokerage Hardening",
        account_type=AccountType.INVESTMENT,
        currency="INR",
        opening_balance=Decimal("50000.00"),
    )
    asset = InvestmentAsset(
        symbol="HARDEN.NS",
        name="Hardening Asset Ltd",
        asset_type="EQUITY",
        currency="INR",
        is_active=True,
    )
    db_session.add_all([acc, asset])
    db_session.flush()

    # Zero quantity buy
    res_zero_qty = client.post(
        "/api/v1/investments/buy",
        json={
            "account_id": acc.id,
            "asset_id": asset.id,
            "quantity": "0.0000",
            "price_per_unit": "100.00",
        },
    )
    assert res_zero_qty.status_code == 422

    # Negative price buy
    res_neg_price = client.post(
        "/api/v1/investments/buy",
        json={
            "account_id": acc.id,
            "asset_id": asset.id,
            "quantity": "5.0000",
            "price_per_unit": "-100.00",
        },
    )
    assert res_neg_price.status_code == 422


def test_large_numeric_boundary_precision(client: TestClient, db_session: Session) -> None:
    """Verify large numeric amounts (up to 999,999,999,999.99) maintain exact Decimal precision."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="High Net Worth Account",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("100000000000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Large transaction: 899,999,999,999.99
    large_amount = "899999999999.99"
    res = client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "transaction_type": "INCOME",
            "amount": large_amount,
            "description": "Large corporate dividend",
        },
    )
    assert res.status_code == 201
    created_tx = res.json()["data"]
    assert created_tx["amount"] == large_amount

    # Verify reconciliation calculation computes exact Decimal without float precision drift
    rec_res = client.get(f"/api/v1/transactions/reconcile/{acc.id}")
    assert rec_res.status_code == 200
    expected_balance = str(Decimal("100000000000.00") + Decimal("899999999999.99"))
    assert rec_res.json()["data"]["current_balance"] == expected_balance


def test_currency_mismatch_transfer_rejection(client: TestClient, db_session: Session) -> None:
    """Verify transfers between accounts of different currencies are strictly blocked with HTTP 422."""
    acc_inr = FinancialAccount(
        user_id="default-user-id",
        name="INR Account",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("10000.00"),
    )
    acc_usd = FinancialAccount(
        user_id="default-user-id",
        name="USD Account",
        account_type=AccountType.CHECKING,
        currency="USD",
        opening_balance=Decimal("500.00"),
    )
    db_session.add_all([acc_inr, acc_usd])
    db_session.flush()

    res = client.post(
        "/api/v1/transactions/transfer",
        json={
            "source_account_id": acc_inr.id,
            "destination_account_id": acc_usd.id,
            "amount": "100.00",
            "description": "Cross-currency transfer attempt",
        },
    )
    assert res.status_code == 422
    err_body = res.json()
    assert err_body["success"] is False
    assert err_body["error"]["code"] == "CURRENCY_MISMATCH"


def test_repeated_reversal_rejection(client: TestClient, db_session: Session) -> None:
    """Verify an already-reversed transaction cannot be reversed a second time."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Reversal Test Account",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("2000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    tx_res = client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "transaction_type": "EXPENSE",
            "amount": "250.00",
            "description": "Utility bill payment",
        },
    )
    assert tx_res.status_code == 201
    tx_id = tx_res.json()["data"]["id"]

    # First reversal succeeds
    rev1 = client.post(
        f"/api/v1/transactions/{tx_id}/reverse",
        json={"reason": "First reversal"},
    )
    assert rev1.status_code == 201

    # Second reversal must fail with 422 VALIDATION_ERROR
    rev2 = client.post(
        f"/api/v1/transactions/{tx_id}/reverse",
        json={"reason": "Second reversal attempt"},
    )
    assert rev2.status_code == 422
    assert "already been reversed" in rev2.json()["error"]["message"]


def test_insufficient_investment_units_rejection(client: TestClient, db_session: Session) -> None:
    """Verify liquidating more units than held is rejected with HTTP 422 INSUFFICIENT_UNITS."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Demat Account",
        account_type=AccountType.INVESTMENT,
        currency="INR",
        opening_balance=Decimal("10000.00"),
    )
    asset = InvestmentAsset(
        symbol="INFY.NS",
        name="Infosys Limited",
        asset_type="EQUITY",
        currency="INR",
        is_active=True,
    )
    db_session.add_all([acc, asset])
    db_session.flush()

    # Buy 10 units
    buy_res = client.post(
        "/api/v1/investments/buy",
        json={
            "account_id": acc.id,
            "asset_id": asset.id,
            "quantity": "10.0000",
            "price_per_unit": "1400.00",
        },
    )
    assert buy_res.status_code == 201

    # Attempt to sell 15 units (exceeds holding of 10)
    sell_res = client.post(
        "/api/v1/investments/sell",
        json={
            "account_id": acc.id,
            "asset_id": asset.id,
            "quantity": "15.0000",
            "price_per_unit": "1450.00",
        },
    )
    assert sell_res.status_code == 422
    assert sell_res.json()["error"]["code"] == "INSUFFICIENT_UNITS"


def test_transfer_balance_conservation_and_reversal(
    client: TestClient, db_session: Session
) -> None:
    """Verify double-entry transfer conserves total balance across accounts and restores on reversal."""
    acc_a = FinancialAccount(
        user_id="default-user-id",
        name="Account Alpha",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("5000.00"),
    )
    acc_b = FinancialAccount(
        user_id="default-user-id",
        name="Account Beta",
        account_type=AccountType.SAVINGS,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add_all([acc_a, acc_b])
    db_session.flush()

    # Execute transfer of 1500.00
    res_tx = client.post(
        "/api/v1/transactions/transfer",
        json={
            "source_account_id": acc_a.id,
            "destination_account_id": acc_b.id,
            "amount": "1500.00",
            "description": "Savings allocation",
        },
    )
    assert res_tx.status_code == 201
    transfer_tx_id = res_tx.json()["data"]["id"]

    # Verify balances via reconciliation: A = 3500, B = 2500, Total = 6000
    bal_a = client.get(f"/api/v1/transactions/reconcile/{acc_a.id}").json()["data"][
        "current_balance"
    ]
    bal_b = client.get(f"/api/v1/transactions/reconcile/{acc_b.id}").json()["data"][
        "current_balance"
    ]
    assert bal_a == "3500.00"
    assert bal_b == "2500.00"
    assert Decimal(bal_a) + Decimal(bal_b) == Decimal("6000.00")

    # Reverse the transfer
    rev_res = client.post(
        f"/api/v1/transactions/{transfer_tx_id}/reverse",
        json={"reason": "Compensating transfer reversal"},
    )
    assert rev_res.status_code == 201

    # Verify balances restored: A = 5000, B = 1000, Total = 6000
    bal_a_restored = client.get(f"/api/v1/transactions/reconcile/{acc_a.id}").json()["data"][
        "current_balance"
    ]
    bal_b_restored = client.get(f"/api/v1/transactions/reconcile/{acc_b.id}").json()["data"][
        "current_balance"
    ]
    assert bal_a_restored == "5000.00"
    assert bal_b_restored == "1000.00"
    assert Decimal(bal_a_restored) + Decimal(bal_b_restored) == Decimal("6000.00")


def test_cross_user_tenant_isolation(client: TestClient, db_session: Session) -> None:
    """Verify tenant isolation: User B cannot view, mutate, or reverse User A's financial entities."""
    # User A creates an account and transaction
    user_a_acc = FinancialAccount(
        user_id="default-user-id",
        name="User A Private Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("3000.00"),
    )
    db_session.add(user_a_acc)
    db_session.flush()

    tx_res = client.post(
        "/api/v1/transactions",
        json={
            "account_id": user_a_acc.id,
            "transaction_type": "EXPENSE",
            "amount": "150.00",
            "description": "User A secret expense",
        },
    )
    assert tx_res.status_code == 201
    user_a_tx_id = tx_res.json()["data"]["id"]

    # Create authenticated client for User B
    client_b = create_authenticated_client(
        user_id="user-b-tenant-id",
        email="user_b@isolated.dev",
        name="User B",
        db_session=db_session,
    )

    # 1. User B cannot read User A's account
    acc_read_b = client_b.get(f"/api/v1/accounts/{user_a_acc.id}")
    assert acc_read_b.status_code == 404

    # 2. User B cannot patch User A's account
    acc_patch_b = client_b.patch(
        f"/api/v1/accounts/{user_a_acc.id}", json={"name": "Hacked Account"}
    )
    assert acc_patch_b.status_code == 404

    # 3. User B cannot delete User A's account
    acc_del_b = client_b.delete(f"/api/v1/accounts/{user_a_acc.id}")
    assert acc_del_b.status_code == 404

    # 4. User B cannot read User A's transaction
    tx_read_b = client_b.get(f"/api/v1/transactions/{user_a_tx_id}")
    assert tx_read_b.status_code == 404

    # 5. User B cannot reverse User A's transaction
    tx_rev_b = client_b.post(
        f"/api/v1/transactions/{user_a_tx_id}/reverse",
        json={"reason": "Unauthorized reversal attempt"},
    )
    assert tx_rev_b.status_code == 404


def test_unauthenticated_requests_blocked(unauthenticated_client: TestClient) -> None:
    """Verify endpoints strictly enforce authentication returning HTTP 401 Unauthorized."""
    endpoints = [
        ("GET", "/api/v1/accounts"),
        ("GET", "/api/v1/transactions"),
        ("GET", "/api/v1/budgets/period?month=11&year=2026"),
        ("GET", "/api/v1/goals"),
        ("GET", "/api/v1/loans"),
        ("GET", "/api/v1/investments/holdings"),
        ("GET", "/api/v1/recurring"),
        ("GET", "/api/v1/data/backup"),
    ]
    for method, path in endpoints:
        if method == "GET":
            res = unauthenticated_client.get(path)
        else:
            res = unauthenticated_client.post(path)
        assert res.status_code == 401, f"Endpoint {path} did not return 401 Unauthorized"
        assert "Not authenticated" in str(res.json()) or res.status_code == 401


def test_public_enrollment_endpoint_permanently_absent(client: TestClient) -> None:
    """Verify public enrollment endpoint /api/v1/auth/enroll returns 404 Not Found."""
    res = client.post("/api/v1/auth/enroll", json={"email": "hacker@evil.dev", "password": "pass"})
    assert res.status_code == 404


def test_backup_validation_incompatible_schema_and_malformed_payload(client: TestClient) -> None:
    """Verify backup dry-run validation rejects invalid versions and malformed schemas."""
    # Incompatible schema version
    bad_version_payload = {
        "schema_version": "9.9.9",
        "exported_at": "2026-11-16T00:00:00",
        "data": {},
    }
    res_ver = client.post("/api/v1/data/backup/validate", json=bad_version_payload)
    assert res_ver.status_code == 200
    assert res_ver.json()["data"]["is_valid"] is False
    assert any(
        "Incompatible backup schema version" in m
        for m in res_ver.json()["data"]["validation_messages"]
    )

    # Malformed payload (missing data)
    malformed_payload = {
        "schema_version": "1.0.0",
        "exported_at": "2026-11-16T00:00:00",
    }
    res_mal = client.post("/api/v1/data/backup/validate", json=malformed_payload)
    assert res_mal.status_code == 200
    assert res_mal.json()["data"]["is_valid"] is False
    assert any(
        "Missing or invalid 'data' section" in m
        for m in res_mal.json()["data"]["validation_messages"]
    )
