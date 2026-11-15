"""Frontend views package for Streamlit application."""

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

__all__ = [
    "render_login_view",
    "render_dashboard_view",
    "render_analytics_view",
    "render_accounts_view",
    "render_transactions_view",
    "render_budgets_view",
    "render_goals_view",
    "render_loans_view",
    "render_investments_view",
    "render_recurring_view",
    "render_settings_view",
]
