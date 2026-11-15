"""Unit tests for Streamlit frontend views rendering logic and component interactions."""

from unittest.mock import MagicMock, patch

from src.frontend.views.accounts import render_accounts_view
from src.frontend.views.analytics import render_analytics_view
from src.frontend.views.budgets import render_budgets_view
from src.frontend.views.dashboard import render_dashboard_view
from src.frontend.views.goals import render_goals_view
from src.frontend.views.investments import render_investments_view
from src.frontend.views.loans import render_loans_view
from src.frontend.views.login import render_login_view
from src.frontend.views.recurring import render_recurring_view
from src.frontend.views.settings import render_settings_view
from src.frontend.views.transactions import render_transactions_view


def test_render_login_view_structure() -> None:
    """Verify login view sets up authentication card and displays error messages."""
    mock_session_state = {
        "session_expired": True,
        "auth_error": "Invalid email or password.",
    }
    with (
        patch("streamlit.session_state", mock_session_state),
        patch("streamlit.columns", return_value=[MagicMock(), MagicMock(), MagicMock()]),
        patch("streamlit.form", return_value=MagicMock()),
        patch("streamlit.text_input", side_effect=["user@local.dev", "secret"]),
        patch("streamlit.form_submit_button", return_value=False),
        patch("streamlit.warning") as mock_warn,
        patch("streamlit.error") as mock_err,
    ):
        render_login_view()
        mock_warn.assert_called_once()
        assert "session has expired" in mock_warn.call_args[0][0]
        mock_err.assert_called_once()
        assert "Invalid email or password" in mock_err.call_args[0][0]


def test_render_dashboard_view_aggregates_currencies_without_mixing() -> None:
    """Verify dashboard isolates INR and USD balances without summing across currencies."""
    mock_accounts = [
        {
            "id": "acc-inr",
            "name": "Salary Account",
            "currency": "INR",
            "opening_balance": "50000.00",
        },
        {"id": "acc-usd", "name": "USD Savings", "currency": "USD", "opening_balance": "1500.00"},
    ]
    mock_transactions = {
        "items": [
            {
                "id": "tx-1",
                "transaction_date": "2026-11-01",
                "transaction_type": "INCOME",
                "amount": "10000.00",
                "currency": "INR",
                "description": "Consulting",
            },
            {
                "id": "tx-2",
                "transaction_date": "2026-11-02",
                "transaction_type": "EXPENSE",
                "amount": "2000.00",
                "currency": "INR",
                "description": "Dining",
            },
            {
                "id": "tx-3",
                "transaction_date": "2026-11-03",
                "transaction_type": "TRANSFER",
                "amount": "500.00",
                "currency": "INR",
                "description": "Internal Transfer",
            },
        ],
        "meta": {"total": 3},
    }

    with (
        patch(
            "src.frontend.api_client.api_client.list_accounts", return_value=(True, mock_accounts)
        ),
        patch(
            "src.frontend.api_client.api_client.reconcile_account",
            return_value=(True, {"current_balance": "50000.00"}),
        ),
        patch(
            "src.frontend.api_client.api_client.list_transactions",
            return_value=(True, mock_transactions),
        ),
        patch(
            "src.frontend.api_client.api_client.list_budgets_for_period", return_value=(True, [])
        ),
        patch("streamlit.columns", side_effect=lambda n: [MagicMock() for _ in range(n)]),
        patch("streamlit.metric") as mock_metric,
    ):
        render_dashboard_view()
        # Verify metric calls exist for INR and USD separately
        labels = [call[1]["label"] for call in mock_metric.call_args_list if "label" in call[1]]
        assert any("INR" in lbl for lbl in labels)
        assert any("USD" in lbl for lbl in labels)
        assert "Active Accounts" in labels


def _mock_columns(spec: object) -> list[MagicMock]:
    """Helper mock supporting both integer column counts and ratio sequences."""
    count = spec if isinstance(spec, int) else len(spec)  # type: ignore[arg-type]
    return [MagicMock() for _ in range(count)]


def test_render_accounts_view_renders_tabs_and_accounts() -> None:
    """Verify accounts view lists active accounts and renders creation tab."""
    mock_accounts = [
        {
            "id": "acc-1",
            "name": "Primary Checking",
            "account_type": "CHECKING",
            "currency": "INR",
            "opening_balance": "15000.00",
        },
    ]
    with (
        patch(
            "src.frontend.api_client.api_client.list_accounts", return_value=(True, mock_accounts)
        ),
        patch(
            "src.frontend.api_client.api_client.reconcile_account",
            return_value=(True, {"current_balance": "15000.00"}),
        ),
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock()]),
        patch("streamlit.container", return_value=MagicMock()),
        patch("streamlit.columns", side_effect=_mock_columns),
    ):
        render_accounts_view()


def test_render_transactions_view_empty_accounts_handling() -> None:
    """Verify transactions view alerts user when no accounts are configured."""
    with (
        patch("src.frontend.api_client.api_client.list_accounts", return_value=(True, [])),
        patch("src.frontend.views.transactions.render_empty_state") as mock_empty,
    ):
        render_transactions_view()
        mock_empty.assert_called_once()
        assert "Accounts Required" in mock_empty.call_args[1]["title"]


def test_render_budgets_view_renders_overview() -> None:
    """Verify budgets view queries period budgets and displays utilization."""
    mock_budgets = [
        {
            "id": "b-1",
            "category_id": "cat-groceries",
            "amount": "12000.00",
            "rollover_enabled": False,
        },
    ]
    mock_util = {
        "category_name": "Groceries",
        "budgeted_amount": "12000.00",
        "spent_amount": "6000.00",
        "remaining_amount": "6000.00",
        "utilization_percentage": "50.0",
        "status": "NORMAL",
        "is_overspent": False,
    }

    with (
        patch(
            "src.frontend.api_client.api_client.list_budgets_for_period",
            return_value=(True, mock_budgets),
        ),
        patch(
            "src.frontend.api_client.api_client.get_budget_utilization",
            return_value=(True, mock_util),
        ),
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock()]),
        patch("streamlit.progress") as mock_prog,
    ):
        render_budgets_view()
        mock_prog.assert_called_once_with(0.5)


def test_render_settings_view_displays_profile_and_currency() -> None:
    """Verify settings view presents profile data, INR default currency, and logout."""
    mock_session_state = {
        "user_profile": {
            "id": "test-uuid-456",
            "name": "Jane Doe",
            "email": "jane@example.dev",
            "created_at": "2026-11-15T12:00:00",
        }
    }
    with (
        patch("streamlit.session_state", mock_session_state),
        patch("streamlit.button", return_value=False) as mock_btn,
    ):
        render_settings_view()
        mock_btn.assert_called_once()
        assert "Log Out" in mock_btn.call_args[0][0]


def test_render_goals_view() -> None:
    """Verify savings goals view handles empty state and populated milestones with progress."""
    # 1. Empty state
    with (
        patch("src.frontend.api_client.api_client.list_goals", return_value=(True, [])),
        patch("src.frontend.views.goals.render_empty_state") as mock_empty,
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock()]),
    ):
        render_goals_view()
        mock_empty.assert_called_once()
        assert "No Savings Goals" in mock_empty.call_args[1]["title"]

    # 2. Populated goals
    mock_goals = [
        {
            "id": "goal-1",
            "name": "Emergency Fund",
            "target_amount": "100000.00",
            "current_amount": "40000.00",
            "currency": "INR",
            "is_achieved": False,
            "target_date": "2027-01-01",
            "notes": "Liquid safety buffer",
        }
    ]
    with (
        patch("src.frontend.api_client.api_client.list_goals", return_value=(True, mock_goals)),
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock()]),
        patch("streamlit.container", return_value=MagicMock()),
        patch("streamlit.progress") as mock_prog,
        patch("streamlit.expander", return_value=MagicMock()),
        patch("streamlit.columns", side_effect=_mock_columns),
    ):
        render_goals_view()
        mock_prog.assert_called_once_with(0.4)


def test_render_loans_view() -> None:
    """Verify loans view handles empty state and displays loan liabilities with amortization schedules."""
    # 1. Empty state
    with (
        patch("src.frontend.api_client.api_client.list_loans", return_value=(True, [])),
        patch("src.frontend.views.loans.render_empty_state") as mock_empty,
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock()]),
    ):
        render_loans_view()
        mock_empty.assert_called_once()
        assert "No Loan Liabilities" in mock_empty.call_args[1]["title"]

    # 2. Populated loans
    mock_loans = [
        {
            "id": "loan-1",
            "lender_name": "HDFC Bank",
            "principal_amount": "500000.00",
            "remaining_balance": "400000.00",
            "interest_rate": "8.50",
            "term_months": 36,
            "minimum_monthly_payment": "15780.00",
            "is_settled": False,
            "start_date": "2026-01-01",
            "notes": "Fixed vehicle loan",
        }
    ]
    mock_details = {
        "id": "loan-1",
        "payment_schedules": [
            {
                "payment_number": 1,
                "due_date": "2026-02-01",
                "principal_component": "12000.00",
                "interest_component": "3780.00",
                "total_payment": "15780.00",
                "remaining_balance": "488000.00",
                "is_paid": False,
            }
        ],
    }
    with (
        patch("src.frontend.api_client.api_client.list_loans", return_value=(True, mock_loans)),
        patch("src.frontend.api_client.api_client.get_loan", return_value=(True, mock_details)),
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock()]),
        patch("streamlit.container", return_value=MagicMock()),
        patch("streamlit.expander", return_value=MagicMock()),
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.dataframe") as mock_df,
    ):
        render_loans_view()
        mock_df.assert_called_once()


def test_render_investments_view() -> None:
    """Verify investments view presents portfolio holdings and disclaimer."""
    mock_accounts = [{"id": "acc-inv-1", "name": "Zerodha Demat", "currency": "INR"}]
    # 1. Empty holdings
    with (
        patch(
            "src.frontend.api_client.api_client.list_accounts", return_value=(True, mock_accounts)
        ),
        patch("src.frontend.api_client.api_client.list_holdings", return_value=(True, [])),
        patch("src.frontend.views.investments.render_empty_state") as mock_empty,
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()]),
    ):
        render_investments_view()
        mock_empty.assert_called_once()
        assert "No Active Holdings" in mock_empty.call_args[1]["title"]

    # 2. Populated holdings
    mock_holdings = [
        {
            "id": "h-1",
            "account_id": "acc-inv-1",
            "asset_id": "asset-rel",
            "quantity": "25.0000",
            "cost_basis_per_unit": "2400.00",
            "total_cost": "60000.00",
            "currency": "INR",
            "asset": {
                "symbol": "RELIANCE",
                "name": "Reliance Industries Ltd",
                "asset_type": "EQUITY",
            },
        }
    ]
    with (
        patch(
            "src.frontend.api_client.api_client.list_accounts", return_value=(True, mock_accounts)
        ),
        patch(
            "src.frontend.api_client.api_client.list_holdings", return_value=(True, mock_holdings)
        ),
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()]),
        patch("streamlit.container", return_value=MagicMock()),
        patch("streamlit.columns", side_effect=_mock_columns),
    ):
        render_investments_view()


def test_render_recurring_view() -> None:
    """Verify recurring view renders due executions, rules directory, and controls."""
    mock_due = [
        {
            "id": "rule-due-1",
            "name": "Cloud Storage",
            "amount": "800.00",
            "currency": "INR",
            "next_occurrence": "2026-11-15",
        }
    ]
    mock_rules = [
        {
            "id": "rule-due-1",
            "name": "Cloud Storage",
            "amount": "800.00",
            "currency": "INR",
            "transaction_type": "EXPENSE",
            "frequency": "MONTHLY",
            "interval": 1,
            "next_occurrence": "2026-11-15",
            "is_active": True,
        }
    ]
    with (
        patch(
            "src.frontend.api_client.api_client.list_due_recurring_rules",
            return_value=(True, mock_due),
        ),
        patch(
            "src.frontend.api_client.api_client.list_recurring_rules",
            return_value=(True, mock_rules),
        ),
        patch("src.frontend.api_client.api_client.list_accounts", return_value=(True, [])),
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock()]),
        patch("streamlit.container", return_value=MagicMock()),
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.button", return_value=False) as mock_btn,
    ):
        render_recurring_view()
        # Verify execution and pause buttons were presented
        assert mock_btn.call_count >= 2


def test_render_analytics_view() -> None:
    """Verify analytics view computes cash flow metrics, renders charts, and handles AI toggle."""
    mock_txs = {
        "items": [
            {
                "id": "tx-1",
                "transaction_type": "INCOME",
                "amount": "50000.00",
                "currency": "INR",
                "transaction_date": "2026-11-01",
                "description": "Salary",
            },
            {
                "id": "tx-2",
                "transaction_type": "EXPENSE",
                "amount": "20000.00",
                "currency": "INR",
                "transaction_date": "2026-11-02",
                "description": "Groceries",
                "category": "Groceries",
            },
        ],
        "meta": {"total": 2},
    }
    with (
        patch("src.frontend.api_client.api_client.list_accounts", return_value=(True, [])),
        patch(
            "src.frontend.api_client.api_client.list_transactions", return_value=(True, mock_txs)
        ),
        patch("src.frontend.api_client.api_client.list_goals", return_value=(True, [])),
        patch("src.frontend.api_client.api_client.list_loans", return_value=(True, [])),
        patch("src.frontend.api_client.api_client.list_holdings", return_value=(True, [])),
        patch("src.frontend.api_client.api_client.list_recurring_rules", return_value=(True, [])),
        patch(
            "src.frontend.api_client.api_client.list_budgets_for_period", return_value=(True, [])
        ),
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.selectbox", side_effect=["INR", "Last 6 Months", "All Accounts"]),
        patch(
            "streamlit.tabs",
            return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()],
        ),
        patch("streamlit.metric") as mock_metric,
        patch("streamlit.plotly_chart") as mock_plot,
        patch("streamlit.toggle", return_value=True),
    ):
        render_analytics_view()
        # Metric cards called for Income, Expense, Net Flow, Savings Rate
        assert mock_metric.call_count >= 4
        # Plotly charts rendered
        assert mock_plot.call_count >= 1
