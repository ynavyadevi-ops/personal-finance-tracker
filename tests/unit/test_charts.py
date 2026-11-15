"""Unit tests for Plotly chart generators: empty states, layout properties, and traces."""

from decimal import Decimal

import plotly.graph_objects as go

from src.frontend.components.charts import (
    create_budget_vs_actual_chart,
    create_cash_flow_trend_chart,
    create_category_donut_chart,
    create_empty_chart,
    create_income_expense_bar_chart,
    create_investment_allocation_chart,
    create_savings_progress_chart,
)


def test_create_empty_chart() -> None:
    """Verify empty chart generates annotation message and hidden axes."""
    fig = create_empty_chart("Empty Test", "Nothing to display")
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text == "Empty Test"
    assert fig.layout.annotations[0].text == "Nothing to display"


def test_create_income_expense_bar_chart() -> None:
    """Verify grouped bar chart with income and expense series."""
    monthly_data = [
        {"month": "2026-09", "income": Decimal("50000.00"), "expense": Decimal("30000.00")},
        {"month": "2026-10", "income": Decimal("55000.00"), "expense": Decimal("32000.00")},
    ]
    fig = create_income_expense_bar_chart(monthly_data, currency="INR")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert fig.data[0].name == "Income"
    assert fig.data[1].name == "Expenses"


def test_create_cash_flow_trend_chart() -> None:
    """Verify net cash flow trend scatter chart."""
    monthly_data = [
        {"month": "2026-09", "net_flow": Decimal("20000.00")},
        {"month": "2026-10", "net_flow": Decimal("23000.00")},
    ]
    fig = create_cash_flow_trend_chart(monthly_data, currency="INR")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].name == "Net Flow"


def test_create_category_donut_chart() -> None:
    """Verify donut pie chart for expense distribution."""
    cat_data = [
        {"category": "Rent", "amount": Decimal("20000.00")},
        {"category": "Groceries", "amount": Decimal("10000.00")},
    ]
    fig = create_category_donut_chart(cat_data, currency="INR")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].hole == 0.55


def test_create_budget_vs_actual_chart() -> None:
    """Verify horizontal comparison chart for budget limits vs actuals."""
    b_data = [
        {
            "category_name": "Groceries",
            "budgeted_amount": Decimal("12000.00"),
            "spent_amount": Decimal("10000.00"),
        }
    ]
    fig = create_budget_vs_actual_chart(b_data, currency="INR")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_create_savings_progress_chart() -> None:
    """Verify stacked bar chart for savings milestone completion."""
    goals = [
        {
            "name": "Emergency Fund",
            "current_amount": Decimal("80000.00"),
            "remaining_amount": Decimal("20000.00"),
        }
    ]
    fig = create_savings_progress_chart(goals, currency="INR")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_create_investment_allocation_chart() -> None:
    """Verify investment portfolio cost basis allocation chart."""
    holdings = [
        {"symbol": "RELIANCE", "total_cost": Decimal("50000.00")},
        {"symbol": "TCS", "total_cost": Decimal("30000.00")},
    ]
    fig = create_investment_allocation_chart(holdings, currency="INR")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].hole == 0.55
