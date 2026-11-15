"""Unit tests for Streamlit ApiClient and frontend helper components."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import httpx

from src.frontend.api_client import ApiClient
from src.frontend.components.ui import PALETTE, format_money, render_badge


def test_api_client_initialization() -> None:
    """Verify ApiClient constructs endpoints and manages token property properly."""
    client = ApiClient(base_url="http://127.0.0.1:8000/api/v1")
    assert client.base_url == "http://127.0.0.1:8000/api/v1"
    assert client.root_url == "http://127.0.0.1:8000"
    assert client.token is None

    client.token = "test-token-xyz"
    assert client.token == "test-token-xyz"
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer test-token-xyz"
    assert headers["Content-Type"] == "application/json"

    # Non-json headers (e.g. form-urlencoded)
    form_headers = client._get_headers(is_json=False)
    assert "Content-Type" not in form_headers
    assert form_headers["Authorization"] == "Bearer test-token-xyz"


def test_api_client_handles_unreachable_server() -> None:
    """Verify ApiClient returns clean error tuples on connection failure."""
    client = ApiClient(base_url="http://127.0.0.1:54321/api/v1", timeout=0.5)
    is_healthy, data = client.check_health()
    assert is_healthy is False
    assert "Cannot connect" in data.get("message", "")
    assert data.get("code") == "CONNECTION_ERROR"

    ok, accounts = client.list_accounts()
    assert ok is False
    assert accounts == []


def test_api_client_login_success() -> None:
    """Verify login successfully exchanges credentials for Bearer token."""
    client = ApiClient(base_url="http://testserver/api/v1")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "mock-jwt-token-abc",
        "token_type": "bearer",
        "expires_in": 3600,
    }

    with patch.object(httpx.Client, "post", return_value=mock_resp):
        success, result = client.login(username="user@local.dev", password="Password123!")
        assert success is True
        assert result["access_token"] == "mock-jwt-token-abc"
        assert client.token == "mock-jwt-token-abc"


def test_api_client_login_failure() -> None:
    """Verify login failure extracts structured error response."""
    client = ApiClient(base_url="http://testserver/api/v1")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"
    mock_resp.json.return_value = {
        "success": False,
        "error": {"code": "UNAUTHORIZED", "message": "Invalid email or password."},
    }

    with patch.object(httpx.Client, "post", return_value=mock_resp):
        success, result = client.login(username="wrong@local.dev", password="WrongPassword")
        assert success is False
        assert result["code"] == "UNAUTHORIZED"
        assert result["message"] == "Invalid email or password."


def test_api_client_get_current_user() -> None:
    """Verify get_current_user retrieves profile with Bearer authorization."""
    client = ApiClient(base_url="http://testserver/api/v1", token="valid-token")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "data": {
            "id": "user-uuid-123",
            "name": "Primary User",
            "email": "user@local.dev",
        },
    }

    with patch.object(httpx.Client, "get", return_value=mock_resp) as mock_get:
        success, user_data = client.get_current_user()
        assert success is True
        assert user_data["id"] == "user-uuid-123"
        mock_get.assert_called_once()
        headers = mock_get.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer valid-token"


def test_api_client_account_operations() -> None:
    """Verify account listing, retrieval, creation, updating, archiving, and reconciliation."""
    client = ApiClient(base_url="http://testserver/api/v1", token="test-token")

    # 1. List accounts
    mock_list = MagicMock(spec=httpx.Response)
    mock_list.status_code = 200
    mock_list.json.return_value = {
        "success": True,
        "data": [{"id": "acc-1", "name": "Checking", "currency": "INR"}],
    }

    with patch.object(httpx.Client, "get", return_value=mock_list):
        ok, accounts = client.list_accounts()
        assert ok is True
        assert len(accounts) == 1
        assert accounts[0]["name"] == "Checking"

    # 2. Get single account
    mock_get = MagicMock(spec=httpx.Response)
    mock_get.status_code = 200
    mock_get.json.return_value = {
        "success": True,
        "data": {"id": "acc-1", "name": "Checking", "currency": "INR"},
    }

    with patch.object(httpx.Client, "get", return_value=mock_get):
        ok, account = client.get_account("acc-1")
        assert ok is True
        assert account["id"] == "acc-1"

    # 3. Create account
    mock_create = MagicMock(spec=httpx.Response)
    mock_create.status_code = 201
    mock_create.json.return_value = {
        "success": True,
        "data": {"id": "acc-new", "name": "Savings", "currency": "INR"},
    }

    with patch.object(httpx.Client, "post", return_value=mock_create):
        ok, created = client.create_account({"name": "Savings", "account_type": "SAVINGS"})
        assert ok is True
        assert created["id"] == "acc-new"

    # 4. Update account
    mock_update = MagicMock(spec=httpx.Response)
    mock_update.status_code = 200
    mock_update.json.return_value = {
        "success": True,
        "data": {"id": "acc-1", "name": "Checking Renamed"},
    }

    with patch.object(httpx.Client, "put", return_value=mock_update):
        ok, updated = client.update_account("acc-1", {"name": "Checking Renamed"})
        assert ok is True
        assert updated["name"] == "Checking Renamed"

    # 5. Archive account
    mock_delete = MagicMock(spec=httpx.Response)
    mock_delete.status_code = 200
    mock_delete.json.return_value = {"success": True, "data": {"id": "acc-1", "is_active": False}}

    with patch.object(httpx.Client, "delete", return_value=mock_delete):
        ok, archived = client.archive_account("acc-1")
        assert ok is True
        assert archived["is_active"] is False

    # 6. Reconcile account
    mock_rec = MagicMock(spec=httpx.Response)
    mock_rec.status_code = 200
    mock_rec.json.return_value = {
        "success": True,
        "data": {"account_id": "acc-1", "current_balance": "1500.00", "is_reconciled": True},
    }

    with patch.object(httpx.Client, "get", return_value=mock_rec):
        ok, rec = client.reconcile_account("acc-1")
        assert ok is True
        assert rec["current_balance"] == "1500.00"


def test_api_client_transaction_operations() -> None:
    """Verify transaction listing, creation, transfer execution, and reversal."""
    client = ApiClient(base_url="http://testserver/api/v1", token="test-token")

    # 1. List transactions
    mock_list = MagicMock(spec=httpx.Response)
    mock_list.status_code = 200
    mock_list.json.return_value = {
        "success": True,
        "data": [{"id": "tx-1", "amount": "500.00", "transaction_type": "EXPENSE"}],
        "meta": {"total": 1, "page": 1, "pages": 1},
    }

    with patch.object(httpx.Client, "get", return_value=mock_list):
        ok, tx_dict = client.list_transactions(page=1, page_size=20)
        assert ok is True
        assert len(tx_dict["items"]) == 1
        assert tx_dict["meta"]["total"] == 1

    # 2. Get single transaction
    mock_get = MagicMock(spec=httpx.Response)
    mock_get.status_code = 200
    mock_get.json.return_value = {
        "success": True,
        "data": {"id": "tx-1", "description": "Coffee"},
    }

    with patch.object(httpx.Client, "get", return_value=mock_get):
        ok, tx = client.get_transaction("tx-1")
        assert ok is True
        assert tx["description"] == "Coffee"

    # 3. Create transaction
    mock_create = MagicMock(spec=httpx.Response)
    mock_create.status_code = 201
    mock_create.json.return_value = {
        "success": True,
        "data": {"id": "tx-2", "amount": "1200.00"},
    }

    with patch.object(httpx.Client, "post", return_value=mock_create):
        ok, created = client.create_transaction({"amount": "1200.00", "description": "Groceries"})
        assert ok is True
        assert created["id"] == "tx-2"

    # 4. Create transfer
    mock_transfer = MagicMock(spec=httpx.Response)
    mock_transfer.status_code = 201
    mock_transfer.json.return_value = {
        "success": True,
        "data": {"id": "tx-tr", "transaction_type": "TRANSFER"},
    }

    with patch.object(httpx.Client, "post", return_value=mock_transfer):
        ok, transfer = client.create_transfer(
            {"source_account_id": "acc-1", "destination_account_id": "acc-2"}
        )
        assert ok is True
        assert transfer["transaction_type"] == "TRANSFER"

    # 5. Reverse transaction
    mock_rev = MagicMock(spec=httpx.Response)
    mock_rev.status_code = 200
    mock_rev.json.return_value = {
        "success": True,
        "data": {"id": "tx-rev-comp", "description": "Reversal of tx-1"},
    }

    with patch.object(httpx.Client, "post", return_value=mock_rev):
        ok, rev = client.reverse_transaction("tx-1", reason="Accidental charge")
        assert ok is True
        assert "Reversal" in rev["description"]


def test_api_client_budget_operations() -> None:
    """Verify period budget listing, utilization queries, and budget creation."""
    client = ApiClient(base_url="http://testserver/api/v1", token="test-token")

    # 1. List budgets for period
    mock_list = MagicMock(spec=httpx.Response)
    mock_list.status_code = 200
    mock_list.json.return_value = {
        "success": True,
        "data": [{"id": "b-1", "category_id": "cat-1", "amount": "10000.00"}],
    }

    with patch.object(httpx.Client, "get", return_value=mock_list):
        ok, budgets = client.list_budgets_for_period(year=2026, month=11)
        assert ok is True
        assert len(budgets) == 1
        assert budgets[0]["amount"] == "10000.00"

    # 2. Get budget utilization
    mock_util = MagicMock(spec=httpx.Response)
    mock_util.status_code = 200
    mock_util.json.return_value = {
        "success": True,
        "data": {
            "category_name": "Groceries",
            "budgeted_amount": "10000.00",
            "spent_amount": "4500.00",
            "remaining_amount": "5500.00",
            "utilization_percentage": "45.0",
            "status": "NORMAL",
        },
    }

    with patch.object(httpx.Client, "get", return_value=mock_util):
        ok, util = client.get_budget_utilization("cat-1", year=2026, month=11)
        assert ok is True
        assert util["status"] == "NORMAL"
        assert util["spent_amount"] == "4500.00"

    # 3. Create budget
    mock_create = MagicMock(spec=httpx.Response)
    mock_create.status_code = 201
    mock_create.json.return_value = {
        "success": True,
        "data": {"id": "b-new", "amount": "15000.00"},
    }

    with patch.object(httpx.Client, "post", return_value=mock_create):
        ok, created = client.create_budget(
            {"category_id": "cat-1", "year": 2026, "month": 11, "amount": "15000.00"}
        )
        assert ok is True
        assert created["id"] == "b-new"


def test_format_money_inr_default() -> None:
    """Verify format_money formats Indian Rupees with ₹ symbol and 2 decimal precision."""
    assert format_money(Decimal("1250.50")) == "₹1,250.50"
    assert format_money("500000.00", "INR") == "₹500,000.00"
    assert format_money(0, "INR") == "₹0.00"


def test_format_money_usd_isolated() -> None:
    """Verify USD currency formats accurately with $ symbol without cross-currency mutation."""
    assert format_money(Decimal("1500.00"), "USD") == "$1,500.00"
    assert format_money("49.99", "USD") == "$49.99"


def test_format_money_other_currencies() -> None:
    """Verify EUR, GBP, and arbitrary currency formatting."""
    assert format_money(Decimal("250.00"), "EUR") == "€250.00"
    assert format_money(Decimal("100.00"), "GBP") == "£100.00"
    assert format_money(Decimal("75.00"), "CAD") == "CAD 75.00"


def test_format_money_negative_values() -> None:
    """Verify negative monetary amounts preserve sign formatting."""
    assert format_money(Decimal("-450.75"), "INR") == "-₹450.75"
    assert format_money(Decimal("-12.50"), "USD") == "-$12.50"


def test_ui_render_badge_and_palette() -> None:
    """Verify badge rendering returns valid HTML with appropriate CSS class."""
    badge_html = render_badge("ACTIVE", "positive")
    assert '<span class="badge badge-positive">ACTIVE</span>' == badge_html

    warning_badge = render_badge("WARNING", "warning")
    assert '<span class="badge badge-warning">WARNING</span>' == warning_badge

    assert PALETTE["bg"] == "#0B1120"
    assert PALETTE["surface"] == "#151E30"
    assert PALETTE["accent"] == "#38BDF8"


def test_api_client_goal_operations() -> None:
    """Verify savings goals listing, creation, progress tracking, contributions, and withdrawals."""
    client = ApiClient(base_url="http://testserver/api/v1", token="test-token")

    # 1. List goals
    mock_list = MagicMock(spec=httpx.Response)
    mock_list.status_code = 200
    mock_list.json.return_value = {
        "success": True,
        "data": [
            {
                "id": "goal-1",
                "name": "Emergency Fund",
                "target_amount": "100000.00",
                "current_amount": "25000.00",
                "currency": "INR",
                "is_achieved": False,
            }
        ],
    }
    with patch.object(httpx.Client, "get", return_value=mock_list):
        ok, goals = client.list_goals()
        assert ok is True
        assert len(goals) == 1
        assert goals[0]["name"] == "Emergency Fund"

    # 2. Create goal
    mock_create = MagicMock(spec=httpx.Response)
    mock_create.status_code = 201
    mock_create.json.return_value = {
        "success": True,
        "data": {"id": "goal-2", "name": "Vacation Fund", "target_amount": "50000.00"},
    }
    with patch.object(httpx.Client, "post", return_value=mock_create):
        ok, created = client.create_goal({"name": "Vacation Fund", "target_amount": "50000.00"})
        assert ok is True
        assert created["id"] == "goal-2"

    # 3. Get progress
    mock_prog = MagicMock(spec=httpx.Response)
    mock_prog.status_code = 200
    mock_prog.json.return_value = {
        "success": True,
        "data": {
            "goal_id": "goal-1",
            "progress_percentage": "25.0",
            "remaining_amount": "75000.00",
        },
    }
    with patch.object(httpx.Client, "get", return_value=mock_prog):
        ok, prog = client.get_goal_progress("goal-1")
        assert ok is True
        assert prog["progress_percentage"] == "25.0"

    # 4. Contribute
    mock_contrib = MagicMock(spec=httpx.Response)
    mock_contrib.status_code = 200
    mock_contrib.json.return_value = {
        "success": True,
        "data": {"goal_id": "goal-1", "current_amount": "30000.00"},
    }
    with patch.object(httpx.Client, "post", return_value=mock_contrib):
        ok, contrib_res = client.contribute_to_goal("goal-1", "5000.00")
        assert ok is True
        assert contrib_res["current_amount"] == "30000.00"

    # 5. Withdraw
    mock_with = MagicMock(spec=httpx.Response)
    mock_with.status_code = 200
    mock_with.json.return_value = {
        "success": True,
        "data": {"goal_id": "goal-1", "current_amount": "20000.00"},
    }
    with patch.object(httpx.Client, "post", return_value=mock_with):
        ok, with_res = client.withdraw_from_goal("goal-1", "10000.00")
        assert ok is True
        assert with_res["current_amount"] == "20000.00"


def test_api_client_loan_operations() -> None:
    """Verify loan liabilities listing, details retrieval, creation, and payment recording."""
    client = ApiClient(base_url="http://testserver/api/v1", token="test-token")

    # 1. List loans
    mock_list = MagicMock(spec=httpx.Response)
    mock_list.status_code = 200
    mock_list.json.return_value = {
        "success": True,
        "data": [
            {
                "id": "loan-1",
                "lender_name": "HDFC Bank",
                "principal_amount": "500000.00",
                "remaining_balance": "480000.00",
                "is_settled": False,
            }
        ],
    }
    with patch.object(httpx.Client, "get", return_value=mock_list):
        ok, loans = client.list_loans()
        assert ok is True
        assert len(loans) == 1
        assert loans[0]["lender_name"] == "HDFC Bank"

    # 2. Get loan details with schedules
    mock_get = MagicMock(spec=httpx.Response)
    mock_get.status_code = 200
    mock_get.json.return_value = {
        "success": True,
        "data": {
            "id": "loan-1",
            "lender_name": "HDFC Bank",
            "payment_schedules": [{"payment_number": 1, "is_paid": False}],
        },
    }
    with patch.object(httpx.Client, "get", return_value=mock_get):
        ok, loan = client.get_loan("loan-1")
        assert ok is True
        assert len(loan["payment_schedules"]) == 1

    # 3. Create loan
    mock_create = MagicMock(spec=httpx.Response)
    mock_create.status_code = 201
    mock_create.json.return_value = {
        "success": True,
        "data": {"id": "loan-new", "principal_amount": "300000.00"},
    }
    with patch.object(httpx.Client, "post", return_value=mock_create):
        ok, created = client.create_loan(
            {"account_id": "acc-1", "lender_name": "SBI", "principal_amount": "300000.00"}
        )
        assert ok is True
        assert created["id"] == "loan-new"

    # 4. Record loan payment
    mock_pay = MagicMock(spec=httpx.Response)
    mock_pay.status_code = 200
    mock_pay.json.return_value = {
        "success": True,
        "data": {"loan_id": "loan-1", "remaining_balance": "470000.00"},
    }
    with patch.object(httpx.Client, "post", return_value=mock_pay):
        ok, pay_res = client.record_loan_payment("loan-1", payment_number=1)
        assert ok is True
        assert pay_res["remaining_balance"] == "470000.00"


def test_api_client_investment_operations() -> None:
    """Verify portfolio holdings, buy, sell, and dividend API interactions."""
    client = ApiClient(base_url="http://testserver/api/v1", token="test-token")

    # 1. List holdings
    mock_list = MagicMock(spec=httpx.Response)
    mock_list.status_code = 200
    mock_list.json.return_value = {
        "success": True,
        "data": [
            {
                "id": "h-1",
                "asset_id": "asset-1",
                "quantity": "10.0000",
                "cost_basis_per_unit": "2500.00",
                "total_cost": "25000.00",
                "currency": "INR",
            }
        ],
    }
    with patch.object(httpx.Client, "get", return_value=mock_list):
        ok, holdings = client.list_holdings()
        assert ok is True
        assert len(holdings) == 1
        assert holdings[0]["quantity"] == "10.0000"

    # 2. Buy security
    mock_buy = MagicMock(spec=httpx.Response)
    mock_buy.status_code = 201
    mock_buy.json.return_value = {
        "success": True,
        "data": {"id": "h-1", "quantity": "15.0000", "total_cost": "37500.00"},
    }
    with patch.object(httpx.Client, "post", return_value=mock_buy):
        ok, buy_res = client.buy_security(
            {
                "account_id": "acc-1",
                "asset_id": "asset-1",
                "quantity": "5.0000",
                "price_per_unit": "2500.00",
            }
        )
        assert ok is True
        assert buy_res["quantity"] == "15.0000"

    # 3. Sell security
    mock_sell = MagicMock(spec=httpx.Response)
    mock_sell.status_code = 200
    mock_sell.json.return_value = {
        "success": True,
        "data": {
            "asset_symbol": "RELIANCE",
            "quantity_sold": "5.0000",
            "realized_gain_loss": "1250.00",
            "is_gain": True,
        },
    }
    with patch.object(httpx.Client, "post", return_value=mock_sell):
        ok, sell_res = client.sell_security(
            {
                "account_id": "acc-1",
                "asset_id": "asset-1",
                "quantity": "5.0000",
                "price_per_unit": "2750.00",
            }
        )
        assert ok is True
        assert sell_res["realized_gain_loss"] == "1250.00"
        assert sell_res["is_gain"] is True

    # 4. Record dividend
    mock_div = MagicMock(spec=httpx.Response)
    mock_div.status_code = 201
    mock_div.json.return_value = {
        "success": True,
        "data": {"id": "tx-div", "total_amount": "500.00", "transaction_type": "DIVIDEND"},
    }
    with patch.object(httpx.Client, "post", return_value=mock_div):
        ok, div_res = client.record_dividend(
            {"account_id": "acc-1", "asset_id": "asset-1", "amount": "500.00"}
        )
        assert ok is True
        assert div_res["total_amount"] == "500.00"


def test_api_client_recurring_operations() -> None:
    """Verify recurring rules listing, due rule checks, creation, pause, resume, and execution."""
    client = ApiClient(base_url="http://testserver/api/v1", token="test-token")

    # 1. List recurring rules
    mock_list = MagicMock(spec=httpx.Response)
    mock_list.status_code = 200
    mock_list.json.return_value = {
        "success": True,
        "data": [{"id": "rule-1", "name": "Netflix", "amount": "649.00", "is_active": True}],
    }
    with patch.object(httpx.Client, "get", return_value=mock_list):
        ok, rules = client.list_recurring_rules()
        assert ok is True
        assert len(rules) == 1
        assert rules[0]["name"] == "Netflix"

    # 2. List due rules
    mock_due = MagicMock(spec=httpx.Response)
    mock_due.status_code = 200
    mock_due.json.return_value = {
        "success": True,
        "data": [{"id": "rule-1", "name": "Netflix", "next_occurrence": "2026-11-15"}],
    }
    with patch.object(httpx.Client, "get", return_value=mock_due):
        ok, due_rules = client.list_due_recurring_rules()
        assert ok is True
        assert len(due_rules) == 1

    # 3. Create recurring rule
    mock_create = MagicMock(spec=httpx.Response)
    mock_create.status_code = 201
    mock_create.json.return_value = {
        "success": True,
        "data": {"id": "rule-new", "name": "Broadband", "amount": "999.00"},
    }
    with patch.object(httpx.Client, "post", return_value=mock_create):
        ok, created = client.create_recurring_rule(
            {"account_id": "acc-1", "name": "Broadband", "amount": "999.00", "currency": "INR"}
        )
        assert ok is True
        assert created["id"] == "rule-new"

    # 4. Execute due rule
    mock_exec = MagicMock(spec=httpx.Response)
    mock_exec.status_code = 201
    mock_exec.json.return_value = {
        "success": True,
        "data": {"transaction_id": "tx-rec-1", "description": "Recurring: Netflix"},
    }
    with patch.object(httpx.Client, "post", return_value=mock_exec):
        ok, ex_res = client.execute_due_rule("rule-1")
        assert ok is True
        assert ex_res["transaction_id"] == "tx-rec-1"

    # 5. Pause rule
    mock_pause = MagicMock(spec=httpx.Response)
    mock_pause.status_code = 200
    mock_pause.json.return_value = {"success": True, "data": {"id": "rule-1", "is_active": False}}
    with patch.object(httpx.Client, "post", return_value=mock_pause):
        ok, p_res = client.pause_recurring_rule("rule-1")
        assert ok is True
        assert p_res["is_active"] is False

    # 6. Resume rule
    mock_resume = MagicMock(spec=httpx.Response)
    mock_resume.status_code = 200
    mock_resume.json.return_value = {"success": True, "data": {"id": "rule-1", "is_active": True}}
    with patch.object(httpx.Client, "post", return_value=mock_resume):
        ok, r_res = client.resume_recurring_rule("rule-1")
        assert ok is True
        assert r_res["is_active"] is True
