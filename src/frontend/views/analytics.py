"""Analytics and Insights view with interactive Plotly visualizations and privacy-conscious AI insights."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.charts import (
    create_budget_vs_actual_chart,
    create_cash_flow_trend_chart,
    create_category_donut_chart,
    create_income_expense_bar_chart,
    create_investment_allocation_chart,
    create_savings_progress_chart,
)
from src.frontend.components.ui import (
    PALETTE,
    format_money,
    render_badge,
    render_empty_state,
    render_header,
)
from src.services.ai_insights import ai_insights_service
from src.services.analytics_service import analytics_engine


def render_analytics_view() -> None:
    """Render interactive financial analytics, charts, and privacy-first financial insights."""
    render_header(
        title="Financial Analytics & Insights",
        subtitle="Interactive multi-period cash flow visualizations, spending breakdowns, and privacy-first rule-based financial insights.",
        badge_text="Analytics",
        badge_type="accent",
    )

    # =========================================================================
    # GLOBAL FILTER CONTROLS
    # =========================================================================
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])

    with col_f1:
        selected_currency = st.selectbox(
            "Analysis Currency",
            options=["INR", "USD", "EUR", "GBP"],
            index=0,
            help="Strictly isolates analytical calculations to prevent cross-currency distortion.",
        )

    with col_f2:
        period_choice = st.selectbox(
            "Timeframe",
            options=["Last 3 Months", "Last 6 Months", "Last 12 Months", "All Time"],
            index=1,
        )

    today = date.today()
    if period_choice == "Last 3 Months":
        start_date = today - timedelta(days=90)
    elif period_choice == "Last 6 Months":
        start_date = today - timedelta(days=180)
    elif period_choice == "Last 12 Months":
        start_date = today - timedelta(days=365)
    else:
        start_date = None

    # Fetch accounts for account filtering
    acc_ok, accounts = api_client.list_accounts()

    with col_f3:
        acc_options = ["All Accounts"]
        if acc_ok and accounts:
            curr_accs = [a for a in accounts if (a.get("currency") or "INR") == selected_currency]
            acc_options.extend([f"{a['name']} ({a['currency']})" for a in curr_accs])
        selected_acc_label = st.selectbox("Account Filter", options=acc_options, index=0)

    selected_account_id = None
    if selected_acc_label != "All Accounts" and acc_ok and accounts:
        for a in accounts:
            if f"{a['name']} ({a['currency']})" == selected_acc_label:
                selected_account_id = a["id"]
                break

    # =========================================================================
    # DATA RETRIEVAL (VIA API CLIENT)
    # =========================================================================
    tx_ok, tx_resp = api_client.list_transactions(
        account_id=selected_account_id,
        limit=500,
    )
    transactions = tx_resp.get("items", []) if tx_ok and isinstance(tx_resp, dict) else []

    # Filter transactions strictly by selected currency
    curr_txs = [
        t for t in transactions if (t.get("currency") or "INR").strip().upper() == selected_currency
    ]

    # Pre-fetch peripheral entities for holistic analysis
    _, goals = api_client.list_goals()
    _, loans = api_client.list_loans()
    _, holdings = api_client.list_holdings()
    _, recurring_rules = api_client.list_recurring_rules()
    _, budgets = api_client.list_budgets_for_period(year=today.year, month=today.month)

    # Compute utilizations for budgets
    utilizations = []
    if budgets:
        for b in budgets:
            cat_id = b.get("category_id")
            if cat_id:
                u_ok, u_data = api_client.get_budget_utilization(
                    category_id=cat_id, year=today.year, month=today.month
                )
                if u_ok and isinstance(u_data, dict):
                    utilizations.append(u_data)

    # =========================================================================
    # ANALYTICS CALCULATIONS
    # =========================================================================
    cash_flow = analytics_engine.calculate_cash_flow(
        curr_txs,
        currency=selected_currency,
        start_date=start_date,
        end_date=today,
    )
    category_spending = analytics_engine.calculate_spending_by_category(
        curr_txs,
        currency=selected_currency,
        start_date=start_date,
        end_date=today,
    )
    monthly_trends = analytics_engine.calculate_monthly_trends(
        curr_txs,
        currency=selected_currency,
        months_count=6 if period_choice != "Last 12 Months" else 12,
    )
    budget_vs_actual = analytics_engine.calculate_budget_vs_actual(budgets or [], utilizations)
    savings_progress = analytics_engine.calculate_savings_progress(goals or [])
    inv_summary = analytics_engine.calculate_investment_cost_basis_summary(
        holdings or [], currency=selected_currency
    )

    # =========================================================================
    # TABS INTERFACE
    # =========================================================================
    tab_cf, tab_cats, tab_budgets, tab_debt_inv, tab_insights = st.tabs(
        [
            "📊 Cash Flow & Trends",
            "🍩 Category Spending",
            "🎯 Budgets & Milestones",
            "📉 Debts & Portfolio",
            "💡 Smart Insights & AI Privacy",
        ]
    )

    # =========================================================================
    # TAB 1: CASH FLOW & TRENDS
    # =========================================================================
    with tab_cf:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric(
                label=f"Total Income ({selected_currency})",
                value=format_money(cash_flow["total_income"], selected_currency),
            )
        with col_m2:
            st.metric(
                label=f"Total Expenses ({selected_currency})",
                value=format_money(cash_flow["total_expense"], selected_currency),
            )
        with col_m3:
            net_val = cash_flow["net_cash_flow"]
            st.metric(
                label=f"Net Cash Flow ({selected_currency})",
                value=format_money(net_val, selected_currency),
                delta=f"{'+' if net_val >= 0 else ''}{net_val:,.2f}",
                delta_color="normal" if net_val >= 0 else "inverse",
            )
        with col_m4:
            st.metric(
                label="Savings Rate",
                value=f"{cash_flow['savings_rate_pct']}%",
            )

        st.caption(
            "Note: Inter-account transfers and reversed transactions are strictly excluded from income and expenses in accordance with double-entry accounting rules."
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_bar = create_income_expense_bar_chart(monthly_trends, selected_currency)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_c2:
            fig_area = create_cash_flow_trend_chart(monthly_trends, selected_currency)
            st.plotly_chart(fig_area, use_container_width=True)

    # =========================================================================
    # TAB 2: CATEGORY SPENDING BREAKDOWN
    # =========================================================================
    with tab_cats:
        if not category_spending:
            render_empty_state(
                title="No Category Expenses Recorded",
                message=f"No expense transactions found for {selected_currency} in the selected timeframe.",
                icon="🍩",
            )
        else:
            col_donut, col_table = st.columns([1, 1])
            with col_donut:
                fig_donut = create_category_donut_chart(category_spending, selected_currency)
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_table:
                st.markdown(f"#### Category Breakdown ({selected_currency})")
                cat_rows = []
                for c in category_spending:
                    cat_rows.append(
                        {
                            "Category": c["category"],
                            "Total Spent": format_money(c["amount"], selected_currency),
                            "Proportion": f"{c['percentage']:.1f}%",
                        }
                    )
                st.dataframe(cat_rows, use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 3: BUDGETS & SAVINGS MILESTONES
    # =========================================================================
    with tab_budgets:
        col_b_chart, col_g_chart = st.columns(2)
        with col_b_chart:
            fig_budget = create_budget_vs_actual_chart(budget_vs_actual, selected_currency)
            st.plotly_chart(fig_budget, use_container_width=True)

        with col_g_chart:
            curr_goals = [g for g in savings_progress if g.get("currency") == selected_currency]
            fig_goals = create_savings_progress_chart(curr_goals, selected_currency)
            st.plotly_chart(fig_goals, use_container_width=True)

    # =========================================================================
    # TAB 4: DEBTS & PORTFOLIO
    # =========================================================================
    with tab_debt_inv:
        # Valuation disclaimer
        st.markdown(
            f"""
            <div style="background-color: {PALETTE["surface_elevated"]}; border-left: 4px solid {PALETTE["accent"]}; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1rem;">
                <div style="font-size: 0.85rem; color: {PALETTE["text"]}; font-weight: 600;">Valuation Notice</div>
                <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]};">
                    Portfolio values represent historical weighted-average cost basis. Real-time market data feeds and speculative live asset values are outside active scope boundaries.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("#### Loan Liabilities")
            if not loans:
                st.info("No loan liabilities recorded.")
            else:
                for loan_item in loans:
                    l_rem = Decimal(str(loan_item.get("remaining_balance", "0.00")))
                    st.markdown(
                        f"""
                        <div class="fintech-card">
                            <div style="display: flex; justify-content: space-between;">
                                <strong>{loan_item.get("lender_name")}</strong>
                                {render_badge("ACTIVE" if l_rem > 0 else "SETTLED", "warning" if l_rem > 0 else "positive")}
                            </div>
                            <div style="font-size: 0.85rem; color: {PALETTE["text_secondary"]}; margin-top: 0.3rem;">
                                Balance: {format_money(l_rem)} • EMI: {format_money(loan_item.get("minimum_monthly_payment", "0.00"))} • Rate: {loan_item.get("interest_rate")}%
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        with col_d2:
            st.markdown("#### Portfolio Allocation (Cost Basis)")
            fig_inv = create_investment_allocation_chart(
                inv_summary["positions"], selected_currency
            )
            st.plotly_chart(fig_inv, use_container_width=True)

    # =========================================================================
    # TAB 5: SMART INSIGHTS & AI PRIVACY
    # =========================================================================
    with tab_insights:
        st.markdown("#### Deterministic Financial Insights")
        st.caption(
            "Rules-based observations calculated directly from your ledger data with fully explainable calculation steps."
        )

        rule_insights = analytics_engine.generate_rule_based_insights(
            transactions=curr_txs,
            budgets=budgets,
            utilizations=utilizations,
            goals=goals,
            loans=loans,
            recurring_rules=recurring_rules,
            currency=selected_currency,
        )

        if not rule_insights:
            render_empty_state(
                title="Sufficient Data Needed for Insights",
                message="Log transactions, budgets, or savings goals to generate automated financial observations.",
                icon="💡",
            )
        else:
            for item in rule_insights:
                badge_type = item.get("severity", "accent")
                st.markdown(
                    f"""
                    <div class="fintech-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                            <span style="font-size: 1.05rem; font-weight: 700; color: {PALETTE["text"]};">
                                {item["title"]}
                            </span>
                            {render_badge(item["category"], badge_type)}
                        </div>
                        <div style="font-size: 0.9rem; color: {PALETTE["text"]}; margin-bottom: 0.4rem;">
                            {item["description"]}
                        </div>
                        <div style="font-size: 0.75rem; color: {PALETTE["text_secondary"]}; font-family: monospace;">
                            📐 How this was derived: {item["calculation"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<hr style='border-color: #334155; margin: 1.5rem 0;'>", unsafe_allow_html=True)

        # AI Insights Section (Privacy-First)
        st.markdown("#### 🤖 AI-Assisted Financial Observations")
        st.markdown(
            f"""
            <div style="background-color: {PALETTE["surface_elevated"]}; border-radius: 8px; padding: 1rem; border: 1px solid {PALETTE["border"]}; margin-bottom: 1rem;">
                <div style="font-size: 0.95rem; font-weight: 700; color: {PALETTE["text"]}; margin-bottom: 0.25rem;">
                    🔒 Privacy-First AI Architecture
                </div>
                <div style="font-size: 0.85rem; color: {PALETTE["text_secondary"]};">
                    AI-assisted analysis is <strong>disabled by default</strong>. When enabled, calculations use only locally aggregated statistics.
                    Zero account credentials, passwords, transaction descriptions, or personally identifiable information are ever transmitted to external cloud models.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_opt_in = st.session_state.get("ai_insights_enabled", False)
        ai_enabled = st.toggle(
            "Enable AI Financial Insights",
            value=current_opt_in,
            key="ai_opt_in_toggle",
            help="Explicit opt-in required. When enabled, generates privacy-safe narrative summaries from de-identified aggregated totals.",
        )
        st.session_state["ai_insights_enabled"] = ai_enabled

        # Prepare sanitized payload
        safe_payload = ai_insights_service.sanitize_for_ai_payload(
            cash_flow=cash_flow,
            category_spending=category_spending,
            savings_rate=cash_flow["savings_rate_pct"],
            currency=selected_currency,
        )

        ai_result = ai_insights_service.generate_ai_narrative(
            aggregated_metrics=safe_payload,
            user_opted_in=ai_enabled,
        )

        if ai_enabled:
            st.markdown(
                f"""
                <div class="fintech-card" style="border-left: 4px solid {PALETTE["accent"]};">
                    <div style="font-size: 1.05rem; font-weight: 700; color: {PALETTE["text"]}; margin-bottom: 0.5rem;">
                        Synthesized Cash Flow Overview
                    </div>
                    <div style="font-size: 0.95rem; color: {PALETTE["text"]}; line-height: 1.5; margin-bottom: 0.75rem;">
                        {ai_result["summary"]}
                    </div>
                    <div style="font-size: 0.75rem; color: {PALETTE["text_secondary"]}; font-style: italic;">
                        ⚠️ {ai_result["disclaimer"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info(ai_result["summary"])
