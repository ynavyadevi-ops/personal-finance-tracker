"""Plotly interactive visualization components adhering to the dark fintech design system."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from src.frontend.components.ui import PALETTE

CHART_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": PALETTE["text"], "family": "Inter, -apple-system, sans-serif"},
    "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
}


def _get_symbol(currency: str) -> str:
    """Return concise display symbol for axis/tooltip formatting."""
    c = (currency or "INR").strip().upper()
    if c == "INR":
        return "₹"
    if c == "USD":
        return "$"
    if c == "EUR":
        return "€"
    if c == "GBP":
        return "£"
    return f"{c} "


def create_empty_chart(title: str, message: str = "No data available for display") -> go.Figure:
    """Return an empty placeholder figure with descriptive text."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 14, "color": PALETTE["text_secondary"]},
    )
    fig.update_layout(
        title={"text": title, "font": {"color": PALETTE["text"], "size": 16}},
        xaxis={"visible": False},
        yaxis={"visible": False},
        **CHART_THEME,
    )
    return fig


def create_income_expense_bar_chart(
    monthly_data: list[dict[str, Any]], currency: str = "INR"
) -> go.Figure:
    """Render grouped bar chart comparing monthly income and expenses."""
    if not monthly_data:
        return create_empty_chart(
            "Monthly Income vs Expenses", "No monthly transaction history found."
        )

    sym = _get_symbol(currency)
    months = [d["month"] for d in monthly_data]
    incomes = [float(d["income"]) for d in monthly_data]
    expenses = [float(d["expense"]) for d in monthly_data]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=months,
            y=incomes,
            name="Income",
            marker_color=PALETTE["positive"],
            hovertemplate=f"Month: %{{x}}<br>Income: {sym}%{{y:,.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=months,
            y=expenses,
            name="Expenses",
            marker_color=PALETTE["negative"],
            hovertemplate=f"Month: %{{x}}<br>Expenses: {sym}%{{y:,.2f}}<extra></extra>",
        )
    )

    fig.update_layout(
        barmode="group",
        title={"text": f"Monthly Income vs Expenses ({currency})", "font": {"size": 16}},
        xaxis={"gridcolor": PALETTE["border"], "tickfont": {"color": PALETTE["text_secondary"]}},
        yaxis={
            "gridcolor": PALETTE["border"],
            "tickfont": {"color": PALETTE["text_secondary"]},
            "tickprefix": sym,
        },
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        **CHART_THEME,
    )
    return fig


def create_cash_flow_trend_chart(
    monthly_data: list[dict[str, Any]], currency: str = "INR"
) -> go.Figure:
    """Render net cash flow line and area trend over time."""
    if not monthly_data:
        return create_empty_chart("Net Cash Flow Trend", "No cash flow data available.")

    sym = _get_symbol(currency)
    months = [d["month"] for d in monthly_data]
    net_flows = [float(d["net_flow"]) for d in monthly_data]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=months,
            y=net_flows,
            mode="lines+markers",
            name="Net Flow",
            line={"color": PALETTE["accent"], "width": 3},
            marker={"size": 7, "color": PALETTE["accent"]},
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.15)",
            hovertemplate=f"Month: %{{x}}<br>Net Cash Flow: {sym}%{{y:,.2f}}<extra></extra>",
        )
    )

    fig.update_layout(
        title={"text": f"Net Cash Flow Trajectory ({currency})", "font": {"size": 16}},
        xaxis={"gridcolor": PALETTE["border"], "tickfont": {"color": PALETTE["text_secondary"]}},
        yaxis={
            "gridcolor": PALETTE["border"],
            "tickfont": {"color": PALETTE["text_secondary"]},
            "tickprefix": sym,
            "zeroline": True,
            "zerolinecolor": PALETTE["border"],
            "zerolinewidth": 2,
        },
        **CHART_THEME,
    )
    return fig


def create_category_donut_chart(
    category_data: list[dict[str, Any]], currency: str = "INR"
) -> go.Figure:
    """Render interactive donut chart displaying proportional category spending."""
    if not category_data:
        return create_empty_chart(
            "Category Spending Breakdown", "No expense records found in period."
        )

    sym = _get_symbol(currency)
    labels = [c["category"] for c in category_data]
    values = [float(c["amount"]) for c in category_data]

    colors = [
        "#38BDF8",
        "#818CF8",
        "#C084FC",
        "#F472B6",
        "#FB7185",
        "#FBBF24",
        "#34D399",
        "#2DD4BF",
        "#A78BFA",
        "#94A3B8",
    ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker={"colors": colors[: len(labels)]},
                textinfo="label+percent",
                textposition="outside",
                hovertemplate=f"Category: %{{label}}<br>Spent: {sym}%{{value:,.2f}}<br>Share: %{{percent}}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title={"text": f"Expense Distribution by Category ({currency})", "font": {"size": 16}},
        showlegend=False,
        **CHART_THEME,
    )
    return fig


def create_budget_vs_actual_chart(
    budget_data: list[dict[str, Any]], currency: str = "INR"
) -> go.Figure:
    """Render horizontal comparison bar chart for budgeted limits vs actual expenditure."""
    if not budget_data:
        return create_empty_chart(
            "Budget vs Actual Spending", "No monthly category budgets established."
        )

    sym = _get_symbol(currency)
    categories = [b["category_name"] for b in budget_data]
    budgeted = [float(b["budgeted_amount"]) for b in budget_data]
    spent = [float(b["spent_amount"]) for b in budget_data]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=categories,
            x=budgeted,
            name="Budget Limit",
            orientation="h",
            marker_color=PALETTE["border"],
            hovertemplate=f"Limit: {sym}%{{x:,.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=categories,
            x=spent,
            name="Actual Spent",
            orientation="h",
            marker_color=[
                PALETTE["negative"] if s > b else PALETTE["accent"]
                for s, b in zip(spent, budgeted, strict=False)
            ],
            hovertemplate=f"Spent: {sym}%{{x:,.2f}}<extra></extra>",
        )
    )

    fig.update_layout(
        barmode="group",
        title={"text": f"Budget Caps vs Actual Spending ({currency})", "font": {"size": 16}},
        xaxis={
            "gridcolor": PALETTE["border"],
            "tickfont": {"color": PALETTE["text_secondary"]},
            "tickprefix": sym,
        },
        yaxis={"tickfont": {"color": PALETTE["text"]}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        **CHART_THEME,
    )
    return fig


def create_savings_progress_chart(
    goal_data: list[dict[str, Any]], currency: str = "INR"
) -> go.Figure:
    """Render horizontal stacked bar chart illustrating savings goal funding progress."""
    if not goal_data:
        return create_empty_chart("Savings Goal Progress", "No savings milestones found.")

    sym = _get_symbol(currency)
    names = [g["name"] for g in goal_data]
    funded = [float(g["current_amount"]) for g in goal_data]
    remaining = [float(g["remaining_amount"]) for g in goal_data]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=names,
            x=funded,
            name="Funded",
            orientation="h",
            marker_color=PALETTE["positive"],
            hovertemplate=f"Funded: {sym}%{{x:,.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=names,
            x=remaining,
            name="Remaining Target",
            orientation="h",
            marker_color=PALETTE["surface_elevated"],
            hovertemplate=f"Remaining: {sym}%{{x:,.2f}}<extra></extra>",
        )
    )

    fig.update_layout(
        barmode="stack",
        title={"text": f"Savings Milestones Completion ({currency})", "font": {"size": 16}},
        xaxis={
            "gridcolor": PALETTE["border"],
            "tickfont": {"color": PALETTE["text_secondary"]},
            "tickprefix": sym,
        },
        yaxis={"tickfont": {"color": PALETTE["text"]}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        **CHART_THEME,
    )
    return fig


def create_investment_allocation_chart(
    holdings_data: list[dict[str, Any]], currency: str = "INR"
) -> go.Figure:
    """Render donut chart of portfolio asset allocation by cost basis."""
    if not holdings_data:
        return create_empty_chart(
            "Portfolio Asset Allocation", "No active security positions held."
        )

    sym = _get_symbol(currency)
    labels = [h["symbol"] for h in holdings_data]
    values = [float(h["total_cost"]) for h in holdings_data]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                textinfo="label+percent",
                hovertemplate=f"Asset: %{{label}}<br>Cost Basis: {sym}%{{value:,.2f}}<br>Share: %{{percent}}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title={
            "text": f"Portfolio Allocation by Cost Basis ({currency})",
            "font": {"size": 16},
        },
        showlegend=False,
        **CHART_THEME,
    )
    return fig
