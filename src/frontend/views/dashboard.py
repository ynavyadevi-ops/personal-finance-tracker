"""Dashboard view for financial summaries, account balances, and recent activity."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.ui import (
    PALETTE,
    format_money,
    render_badge,
    render_empty_state,
    render_header,
)


def render_dashboard_view() -> None:
    """Render consolidated financial overview dashboard."""
    render_header(
        title="Financial Overview",
        subtitle="Consolidated real-time view of accounts, cash flow, and monthly budgets.",
        badge_text="Live Dashboard",
        badge_type="accent",
    )

    # 1. Fetch Accounts
    acc_ok, accounts = api_client.list_accounts(active_only=True)
    if not acc_ok:
        st.error("Failed to fetch financial accounts from backend.")
        return

    # Calculate balances grouped by currency without combining different currencies
    currency_balances: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    account_lookup: dict[str, dict[str, str]] = {}
    for acc in accounts:
        acc_id = acc.get("id", "")
        currency = acc.get("currency", "INR").upper()
        account_lookup[acc_id] = {
            "name": acc.get("name", "Unknown Account"),
            "currency": currency,
        }
        # Attempt to get reconciled current balance or fallback to opening_balance
        rec_ok, rec_data = api_client.reconcile_account(acc_id)
        if rec_ok and "current_balance" in rec_data:
            bal = Decimal(str(rec_data["current_balance"]))
        else:
            bal = Decimal(str(acc.get("opening_balance", "0.00")))
        currency_balances[currency] += bal

    # Display KPI Metrics
    st.markdown(
        f"<h4 style='color: {PALETTE['text']}; margin-bottom: 0.75rem;'>Account Balances by Currency</h4>",
        unsafe_allow_html=True,
    )

    # Separate metrics columns for each currency plus total accounts
    metric_cols = st.columns(max(len(currency_balances) + 1, 3))
    with metric_cols[0]:
        st.metric(
            label="Active Accounts",
            value=len(accounts),
            delta="Operational",
        )

    col_idx = 1
    # Sort with INR first, then USD, then others
    sorted_currencies = sorted(
        currency_balances.keys(),
        key=lambda c: (0 if c == "INR" else (1 if c == "USD" else 2), c),
    )
    for curr in sorted_currencies:
        if col_idx < len(metric_cols):
            with metric_cols[col_idx]:
                st.metric(
                    label=f"Total {curr} Assets",
                    value=format_money(currency_balances[curr], currency=curr),
                    delta="Isolated Ledger",
                )
            col_idx += 1

    st.markdown("<hr style='border-color: #334155; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # 2. Monthly Cash Flow Summary (Current Month)
    today = date.today()
    current_year = today.year
    current_month = today.month

    st.markdown(
        f"<h4 style='color: {PALETTE['text']}; margin-bottom: 0.75rem;'>"
        f"Cash Flow Summary — {today.strftime('%B %Y')}</h4>",
        unsafe_allow_html=True,
    )

    # Fetch recent transactions
    tx_ok, tx_data = api_client.list_transactions(page=1, page_size=100)
    monthly_income: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    monthly_expense: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    transactions_list: list[dict] = []

    if tx_ok and isinstance(tx_data, dict):
        transactions_list = tx_data.get("items", [])
        for tx in transactions_list:
            tx_date_str = tx.get("transaction_date")
            if not tx_date_str:
                continue
            try:
                tx_date = date.fromisoformat(tx_date_str)
            except ValueError:
                continue

            if tx_date.year == current_year and tx_date.month == current_month:
                tx_type = tx.get("transaction_type")
                tx_curr = tx.get("currency", "INR").upper()
                amt = Decimal(str(tx.get("amount", "0.00")))

                # Strictly exclude transfers from income and expenses per financial directives
                if tx_type == "INCOME":
                    monthly_income[tx_curr] += amt
                elif tx_type == "EXPENSE":
                    monthly_expense[tx_curr] += amt

    # Render cash flow cards for primary currency (INR default, or USD)
    cf_cols = st.columns(3)
    display_curr = "INR" if ("INR" in currency_balances or not currency_balances) else "USD"

    with cf_cols[0]:
        inc_val = monthly_income[display_curr]
        st.markdown(
            f"""
            <div class="fintech-card" style="border-left: 4px solid {PALETTE["positive"]};">
                <span class="badge badge-positive">Monthly Income ({display_curr})</span>
                <div style="font-size: 1.5rem; font-weight: 700; color: {PALETTE["positive"]}; margin-top: 0.5rem;">
                    +{format_money(inc_val, display_curr)}
                </div>
                <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]}; margin-top: 0.25rem;">
                    Excludes inter-account transfers
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cf_cols[1]:
        exp_val = monthly_expense[display_curr]
        st.markdown(
            f"""
            <div class="fintech-card" style="border-left: 4px solid {PALETTE["negative"]};">
                <span class="badge badge-negative">Monthly Expenses ({display_curr})</span>
                <div style="font-size: 1.5rem; font-weight: 700; color: {PALETTE["negative"]}; margin-top: 0.5rem;">
                    -{format_money(exp_val, display_curr)}
                </div>
                <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]}; margin-top: 0.25rem;">
                    Category allocated outflows
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cf_cols[2]:
        net_val = inc_val - exp_val
        net_color = PALETTE["positive"] if net_val >= 0 else PALETTE["negative"]
        st.markdown(
            f"""
            <div class="fintech-card" style="border-left: 4px solid {PALETTE["accent"]};">
                <span class="badge badge-accent">Net Cash Flow ({display_curr})</span>
                <div style="font-size: 1.5rem; font-weight: 700; color: {net_color}; margin-top: 0.5rem;">
                    {format_money(net_val, display_curr)}
                </div>
                <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]}; margin-top: 0.25rem;">
                    Surplus / Deficit for {today.strftime("%B")}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='border-color: #334155; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # 3. Monthly Budgets Utilization Section
    st.markdown(
        f"<h4 style='color: {PALETTE['text']}; margin-bottom: 0.75rem;'>"
        f"Active Category Budgets — {today.strftime('%B %Y')}</h4>",
        unsafe_allow_html=True,
    )

    budgets_ok, budgets = api_client.list_budgets_for_period(year=current_year, month=current_month)
    if budgets_ok and budgets:
        b_cols = st.columns(min(len(budgets), 3))
        for idx, b in enumerate(budgets):
            cat_id = b.get("category_id", "")
            u_ok, util = api_client.get_budget_utilization(
                category_id=cat_id, year=current_year, month=current_month
            )
            if u_ok:
                cat_name = util.get("category_name", "Budget")
                budgeted = Decimal(str(util.get("budgeted_amount", "0.00")))
                spent = Decimal(str(util.get("spent_amount", "0.00")))
                remaining = Decimal(str(util.get("remaining_amount", "0.00")))
                pct = float(util.get("utilization_percentage", 0.0))
                status = util.get("status", "NORMAL")

                # Badge mapping
                badge_type = (
                    "positive"
                    if status == "NORMAL"
                    else ("warning" if status == "WARNING" else "negative")
                )

                with b_cols[idx % len(b_cols)]:
                    st.markdown(
                        f"""
                        <div class="fintech-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <span style="font-weight: 600; color: {PALETTE["text"]};">{cat_name}</span>
                                {render_badge(status, badge_type)}
                            </div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: {PALETTE["text"]};">
                                {format_money(spent, "INR")} / {format_money(budgeted, "INR")}
                            </div>
                            <div style="font-size: 0.85rem; color: {PALETTE["text_secondary"]}; margin-bottom: 0.5rem;">
                                Remaining: {format_money(remaining, "INR")}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    # Clamped progress bar
                    st.progress(min(max(pct / 100.0, 0.0), 1.0))
    else:
        st.info(
            "No budgets established for this month. Navigate to **Budgets** to configure category limits."
        )

    st.markdown("<hr style='border-color: #334155; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # 4. Recent Transactions Table
    st.markdown(
        f"<h4 style='color: {PALETTE['text']}; margin-bottom: 0.75rem;'>Recent Transactions</h4>",
        unsafe_allow_html=True,
    )

    if transactions_list:
        recent_txs = transactions_list[:10]
        table_rows = []
        for tx in recent_txs:
            tx_type = tx.get("transaction_type", "EXPENSE")
            curr = tx.get("currency", "INR")
            amt = Decimal(str(tx.get("amount", "0.00")))
            acc_name = "—"
            if tx.get("entries"):
                first_acc_id = tx["entries"][0].get("account_id")
                acc_name = account_lookup.get(first_acc_id, {}).get("name", "Account")

            table_rows.append(
                {
                    "Date": tx.get("transaction_date"),
                    "Description": tx.get("description"),
                    "Type": tx_type,
                    "Account": acc_name,
                    "Amount": format_money(amt, curr),
                }
            )

        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        render_empty_state(
            title="No Transactions Recorded",
            message="Record your first income, expense, or transfer from the Transactions view.",
            icon="💳",
        )
