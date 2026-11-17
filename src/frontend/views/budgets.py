"""Budgets view for category limits, utilization progress, and threshold alerts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.ui import (
    PALETTE,
    format_money,
    render_badge,
    render_empty_state,
    render_header,
)


def render_budgets_view() -> None:
    """Render monthly category budget monitoring and configuration view."""
    render_header(
        title="Category Budgets",
        subtitle="Establish monthly category spending caps and monitor dynamic utilization thresholds.",
        badge_text="Budget Controls",
        badge_type="accent",
    )

    today = date.today()

    # Period Selector Controls
    col_sel_m, col_sel_y = st.columns([1, 1])
    with col_sel_m:
        selected_month = st.selectbox(
            "Select Month",
            options=list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda m: date(2026, m, 1).strftime("%B"),
        )
    with col_sel_y:
        selected_year = st.number_input(
            "Select Year",
            min_value=2020,
            max_value=2030,
            value=today.year,
            step=1,
        )

    tab_overview, tab_create = st.tabs(["📊 Budget Overview", "➕ Establish Monthly Budget"])

    # =========================================================================
    # TAB 1: BUDGET OVERVIEW
    # =========================================================================
    with tab_overview:
        b_ok, budgets = api_client.list_budgets_for_period(year=selected_year, month=selected_month)
        if b_ok and budgets:
            st.markdown(
                f"<h4 style='color: {PALETTE['text']}; margin-bottom: 1rem;'>"
                f"Budgets for {date(selected_year, selected_month, 1).strftime('%B %Y')}</h4>",
                unsafe_allow_html=True,
            )

            for b in budgets:
                cat_id = b.get("category_id", "")
                u_ok, util = api_client.get_budget_utilization(
                    category_id=cat_id, year=selected_year, month=selected_month
                )

                if u_ok and isinstance(util, dict):
                    cat_name = util.get("category_name", f"Category {cat_id[:8]}")
                    budgeted = Decimal(str(util.get("budgeted_amount", "0.00")))
                    spent = Decimal(str(util.get("spent_amount", "0.00")))
                    remaining = Decimal(str(util.get("remaining_amount", "0.00")))
                    util_pct = float(util.get("utilization_percentage", 0.0))
                    status = util.get("status", "NORMAL")
                    is_overspent = util.get("is_overspent", False)

                    badge_type = (
                        "positive"
                        if status == "NORMAL"
                        else ("warning" if status == "WARNING" else "negative")
                    )

                    with st.container():
                        st.markdown(
                            f"""
                            <div class="fintech-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                    <div>
                                        <span style="font-size: 1.15rem; font-weight: 700; color: {PALETTE["text"]};">
                                            {cat_name}
                                        </span>
                                        <span style="font-size: 0.8rem; color: {PALETTE["text_secondary"]}; margin-left: 0.5rem;">
                                            Rollover: {"Enabled" if b.get("rollover_enabled") else "Disabled"}
                                        </span>
                                    </div>
                                    <div>
                                        {render_badge(status, badge_type)}
                                        {render_badge("OVERSPENT", "negative") if is_overspent else ""}
                                    </div>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem;">
                                    <span style="color: {PALETTE["text_secondary"]}; font-size: 0.9rem;">
                                        Spent: <b style="color: {PALETTE["text"]};">{format_money(spent, "INR")}</b> / Cap: {format_money(budgeted, "INR")}
                                    </span>
                                    <span style="font-size: 0.95rem; font-weight: 600; color: {PALETTE[badge_type]};">
                                        {util_pct:.1f}% Used ({format_money(remaining, "INR")} Left)
                                    </span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        # Clamped progress bar
                        st.progress(min(max(util_pct / 100.0, 0.0), 1.0))
                        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        else:
            render_empty_state(
                title="No Budgets Established",
                message=f"No category budgets configured for {date(selected_year, selected_month, 1).strftime('%B %Y')}.",
                icon="🎯",
            )

    # =========================================================================
    # TAB 2: ESTABLISH MONTHLY BUDGET
    # =========================================================================
    with tab_create:
        # Query accessible expense categories for selection
        c_ok, categories = api_client.list_categories(category_type="EXPENSE")
        category_options: dict[str, str] = {}
        if c_ok and categories:
            for cat in categories:
                suffix = " (Default)" if cat.get("is_default") else ""
                category_options[cat["id"]] = f"{cat.get('name', 'Unnamed')}{suffix}"

        if not category_options:
            st.warning(
                "⚠️ Unable to load expense categories from the server. "
                "Please verify your connection or try again."
            )
            if st.button("🔄 Retry Loading Categories", key="retry_load_categories"):
                st.rerun()
        else:
            with st.form("create_budget_form", clear_on_submit=True):
                st.markdown(
                    f"<h4 style='color: {PALETTE['text']}; margin-bottom: 1rem;'>Establish Category Cap</h4>",
                    unsafe_allow_html=True,
                )

                col_cat, col_amt = st.columns(2)
                with col_cat:
                    selected_cat_id = st.selectbox(
                        "Expense Category*",
                        options=list(category_options.keys()),
                        format_func=lambda cid: category_options[cid],
                        help="Select an expense category to allocate budget for.",
                    )
                    category_id = selected_cat_id or ""
                with col_amt:
                    budget_amount = st.text_input(
                        "Monthly Budget Cap (₹)*",
                        placeholder="e.g. 12000.00",
                    ).strip()

                col_y, col_m, col_roll = st.columns([1, 1, 1])
                with col_y:
                    b_year = st.number_input(
                        "Budget Year*", min_value=2020, max_value=2030, value=selected_year
                    )
                with col_m:
                    b_month = st.selectbox(
                        "Budget Month*",
                        options=list(range(1, 13)),
                        index=selected_month - 1,
                        format_func=lambda m: date(2026, m, 1).strftime("%B"),
                        key="create_budget_month",
                    )
                with col_roll:
                    st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
                    rollover = st.checkbox(
                        "Enable Rollover", help="Carry forward unspent balance to next month."
                    )

                b_notes = st.text_input(
                    "Notes (Optional)", placeholder="e.g. Adjusted for holiday season"
                ).strip()

                submitted_budget = st.form_submit_button("Save Budget Allocation")
                if submitted_budget:
                    if not category_id:
                        st.error("Expense Category is required.")
                    elif not budget_amount:
                        st.error("Budget amount is required.")
                    else:
                        try:
                            amt_dec = Decimal(budget_amount)
                            if amt_dec <= Decimal("0.00"):
                                st.error("Budget amount must be strictly positive.")
                                return
                        except Exception:
                            st.error("Budget amount must be a valid numerical value.")
                            return

                        b_payload = {
                            "category_id": category_id,
                            "year": int(b_year),
                            "month": int(b_month),
                            "amount": str(amt_dec),
                            "rollover_enabled": rollover,
                            "notes": b_notes if b_notes else None,
                        }

                        b_res_ok, b_res_data = api_client.create_budget(b_payload)
                        if b_res_ok:
                            st.success(
                                f"Budget allocated: {format_money(amt_dec, 'INR')} "
                                f"for {date(int(b_year), int(b_month), 1).strftime('%B %Y')}."
                            )
                            st.rerun()
                        else:
                            st.error(f"Failed to establish budget: {b_res_data.get('message')}")
