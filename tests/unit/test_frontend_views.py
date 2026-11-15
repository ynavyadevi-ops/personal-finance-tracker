"""Unit tests for Streamlit frontend views rendering logic and component interactions."""

from unittest.mock import MagicMock, patch

from src.frontend.views.accounts import render_accounts_view
from src.frontend.views.budgets import render_budgets_view
from src.frontend.views.dashboard import render_dashboard_view
from src.frontend.views.login import render_login_view
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
