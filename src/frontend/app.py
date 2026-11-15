"""Streamlit interactive web dashboard for Personal Finance Tracker."""

from decimal import Decimal

import pandas as pd
import streamlit as st

from src.core.money import format_currency
from src.frontend.api_client import api_client
from src.frontend.components.ui import (
    apply_custom_css,
    render_header,
    render_phase_placeholder,
)

# Page configuration
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply dark fintech theme styles
apply_custom_css()

# Sidebar Navigation
st.sidebar.markdown(
    """
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem;">
        <span style="font-size: 1.5rem;">💸</span>
        <span style="font-size: 1.15rem; font-weight: 700; color: #f0f6fc;">FinanceTracker</span>
    </div>
    """,
    unsafe_allow_html=True,
)

NAV_OPTIONS = [
    "📊 Dashboard",
    "🏦 Accounts",
    "💳 Transactions",
    "🎯 Budgets",
    "🏆 Goals",
    "📉 Loans & Debts",
    "📈 Investments",
    "📊 Analytics",
    "⚙️ Settings",
]

selected_nav = st.sidebar.radio("Navigation", NAV_OPTIONS, label_visibility="collapsed")

# Sidebar Backend Health Probe
st.sidebar.markdown("---")
is_healthy, health_data = api_client.check_health()
if is_healthy:
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #10b981;">
            <span style="height: 8px; width: 8px; background-color: #10b981; border-radius: 50%; display: inline-block;"></span>
            <span>FastAPI: Connected</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    err_text = health_data.get("message", "Offline")
    st.sidebar.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #ef4444;">
            <span style="height: 8px; width: 8px; background-color: #ef4444; border-radius: 50%; display: inline-block;"></span>
            <span>FastAPI: {err_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.caption("Personal Finance Tracker • Phase 1")

# ==============================================================================
# VIEW: Dashboard
# ==============================================================================
if selected_nav == "📊 Dashboard":
    render_header(
        title="Financial Overview",
        subtitle="Consolidated real-time view of your accounts and system status.",
        badge_text="Phase 1 Active",
    )

    # Fetch accounts from FastAPI
    success, accounts = api_client.list_accounts(active_only=True)

    # Key Metrics Bar
    col1, col2, col3, col4 = st.columns(4)

    total_accounts = len(accounts) if success else 0
    total_balance = (
        sum((Decimal(str(acc.get("opening_balance", "0.00"))) for acc in accounts), Decimal("0.00"))
        if success
        else Decimal("0.00")
    )

    with col1:
        st.metric(
            label="Total Accounts",
            value=total_accounts,
            delta="Active" if total_accounts > 0 else "None",
        )
    with col2:
        st.metric(
            label="Total Opening Assets",
            value=format_currency(total_balance),
            delta="Baseline",
        )
    with col3:
        st.metric(
            label="Backend Service",
            value="Online" if is_healthy else "Offline",
            delta="FastAPI 0.115",
        )
    with col4:
        st.metric(
            label="Database Engine",
            value="SQLite (Active)",
            delta="SQLAlchemy 2.0",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Accounts Preview Table
    st.subheader("Configured Accounts")
    if success and accounts:
        table_data = []
        for acc in accounts:
            table_data.append(
                {
                    "Account Name": acc.get("name"),
                    "Type": acc.get("account_type"),
                    "Institution": acc.get("institution_name") or "—",
                    "Currency": acc.get("currency"),
                    "Opening Balance": format_currency(acc.get("opening_balance", "0.00")),
                    "Status": "Active" if acc.get("is_active") else "Archived",
                }
            )
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(
            "No active accounts found. Navigate to the **Accounts** tab to create your first account."
        )

# ==============================================================================
# VIEW: Accounts
# ==============================================================================
elif selected_nav == "🏦 Accounts":
    render_header(
        title="Financial Accounts",
        subtitle="Create, inspect, and manage your asset, liability, and depository accounts.",
        badge_text="Phase 1 Active",
    )

    tab_list, tab_create = st.tabs(["📋 All Accounts", "➕ Add New Account"])

    with tab_list:
        success, accounts = api_client.list_accounts(active_only=True)
        if success and accounts:
            for acc in accounts:
                with st.container():
                    col_info, col_action = st.columns([4, 1])
                    with col_info:
                        curr = acc.get("currency", "INR")
                        sym = "₹" if curr == "INR" else ("$" if curr == "USD" else f"{curr} ")
                        bal = format_currency(
                            acc.get("opening_balance", "0.00"), currency_symbol=sym
                        )
                        st.markdown(
                            f"""
                            <div class="fintech-card">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <h4 style="margin: 0; color: #f0f6fc;">{acc.get("name")}</h4>
                                        <span style="color: #8b949e; font-size: 0.85rem;">
                                            {acc.get("account_type")} • {acc.get("institution_name") or "Self-managed"}
                                        </span>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 1.25rem; font-weight: 700; color: #10b981;">{bal}</div>
                                        <span class="emerald-badge">{acc.get("currency")}</span>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with col_action:
                        st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
                        acc_id = str(acc.get("id", ""))
                        if st.button("Archive", key=f"archive_{acc_id}"):
                            arch_ok, arch_data = api_client.archive_account(acc_id)
                            if arch_ok:
                                st.success(f"Archived {acc.get('name')}")
                                st.rerun()
                            else:
                                st.error(f"Error: {arch_data.get('message')}")
        else:
            st.info("No active accounts found. Switch to the 'Add New Account' tab to create one.")

    with tab_create:
        with st.form("create_account_form", clear_on_submit=True):
            st.subheader("Register a Financial Account")
            col_name, col_type = st.columns(2)
            with col_name:
                acc_name = st.text_input("Account Name*", placeholder="e.g. Primary Checking")
            with col_type:
                acc_type = st.selectbox(
                    "Account Type*",
                    ["CHECKING", "SAVINGS", "CREDIT_CARD", "CASH", "INVESTMENT", "LOAN"],
                )

            col_inst, col_curr, col_bal = st.columns([2, 1, 2])
            with col_inst:
                acc_inst = st.text_input("Institution Name", placeholder="e.g. HDFC, SBI, ICICI")
            with col_curr:
                acc_curr = st.text_input("Currency", value="INR", max_chars=3)
            with col_bal:
                acc_balance = st.text_input("Opening Balance (₹)", value="0.00")

            submitted = st.form_submit_button("Create Account")
            if submitted:
                if not acc_name.strip():
                    st.error("Account Name is required.")
                else:
                    payload = {
                        "name": acc_name.strip(),
                        "account_type": acc_type,
                        "institution_name": acc_inst.strip() if acc_inst else None,
                        "currency": acc_curr.strip().upper(),
                        "opening_balance": acc_balance.strip(),
                    }
                    create_ok, result = api_client.create_account(payload)
                    if create_ok:
                        st.success(f"Successfully created account: {acc_name}")
                        st.rerun()
                    else:
                        st.error(f"Failed to create account: {result.get('message')}")

# ==============================================================================
# VIEW: Transactions (Placeholder for Phase 3/6)
# ==============================================================================
elif selected_nav == "💳 Transactions":
    render_header(
        title="Transaction Ledger",
        subtitle="Record income, expense, and balanced inter-account transfers.",
        badge_text="Phase 3 & 6",
    )
    render_phase_placeholder(
        feature_name="Double-Entry Inspired Ledger",
        target_phase="Phase 3 (Domain Logic) & Phase 6 (UI Pages)",
        description="Comprehensive ledger tracking for income, expenses, and atomic inter-account transfers with category attribution and search filtering.",
    )

# ==============================================================================
# VIEW: Budgets (Placeholder for Phase 3/6)
# ==============================================================================
elif selected_nav == "🎯 Budgets":
    render_header(
        title="Monthly Budgets",
        subtitle="Establish category spending limits and monitor threshold alerts.",
        badge_text="Phase 3 & 6",
    )
    render_phase_placeholder(
        feature_name="Category Budgeting & Visual Alerts",
        target_phase="Phase 3 (Domain Logic) & Phase 6 (UI Pages)",
        description="Monthly category caps, dynamic utilization progress bars (Normal <80%, Warning 80-99%, Exceeded >=100%), and aggregate spending ceilings.",
    )

# ==============================================================================
# VIEW: Goals (Placeholder for Future Scope)
# ==============================================================================
elif selected_nav == "🏆 Goals":
    render_header(
        title="Savings Goals",
        subtitle="Track financial milestones and target funds.",
        badge_text="Future Scope",
    )
    render_phase_placeholder(
        feature_name="Milestone Goal Tracking",
        target_phase="Post-MVP Scope",
        description="Establish target dollar amounts, completion deadlines, and track periodic contributions toward high-priority milestones.",
    )

# ==============================================================================
# VIEW: Loans & Debts (Placeholder for Future Scope)
# ==============================================================================
elif selected_nav == "📉 Loans & Debts":
    render_header(
        title="Loans & Liabilities",
        subtitle="Manage amortization schedules and debt reduction plans.",
        badge_text="Future Scope",
    )
    render_phase_placeholder(
        feature_name="Liability & Amortization Management",
        target_phase="Post-MVP Scope",
        description="Track principal balances, interest rates, and loan payoff trajectories across student loans, mortgages, and credit facilities.",
    )

# ==============================================================================
# VIEW: Investments (Placeholder for Future Scope)
# ==============================================================================
elif selected_nav == "📈 Investments":
    render_header(
        title="Investment Portfolios",
        subtitle="Monitor asset allocation and capital appreciation.",
        badge_text="Future Scope",
    )
    render_phase_placeholder(
        feature_name="Portfolio Analytics",
        target_phase="Post-MVP Scope",
        description="Consolidate taxable and tax-advantaged retirement accounts, monitor asset allocations, and record cost basis valuations.",
    )

# ==============================================================================
# VIEW: Analytics (Placeholder for Phase 7)
# ==============================================================================
elif selected_nav == "📊 Analytics":
    render_header(
        title="Financial Analytics & Reports",
        subtitle="Interactive visual intelligence powered by Plotly and Pandas.",
        badge_text="Phase 7",
    )
    render_phase_placeholder(
        feature_name="Interactive Plotly Visualizations",
        target_phase="Phase 7 (Analytics & Visualizations)",
        description="Time-series net worth trajectory curves, monthly cash flow grouped bar charts (Income vs Expense), and category expense distribution donuts.",
    )

# ==============================================================================
# VIEW: Settings
# ==============================================================================
elif selected_nav == "⚙️ Settings":
    render_header(
        title="System Configuration",
        subtitle="Local environment settings and database metadata.",
        badge_text="Phase 1 Active",
    )

    st.markdown(
        """
        <div class="fintech-card">
            <h4 style="margin-top: 0; color: #f0f6fc;">Active Environment Specifications</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.95rem;">
                <tr style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 0.5rem 0; color: #8b949e;">Application Name</td>
                    <td style="padding: 0.5rem 0; color: #f0f6fc; font-weight: 600;">Personal Finance Tracker</td>
                </tr>
                <tr style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 0.5rem 0; color: #8b949e;">Application Version</td>
                    <td style="padding: 0.5rem 0; color: #f0f6fc; font-weight: 600;">v0.1.0 (Phase 1 Baseline)</td>
                </tr>
                <tr style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 0.5rem 0; color: #8b949e;">Runtime Framework</td>
                    <td style="padding: 0.5rem 0; color: #f0f6fc; font-weight: 600;">Python 3.12 (FastAPI + Streamlit)</td>
                </tr>
                <tr style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 0.5rem 0; color: #8b949e;">Database Layer</td>
                    <td style="padding: 0.5rem 0; color: #f0f6fc; font-weight: 600;">SQLite (data/finance.db) + SQLAlchemy 2.0</td>
                </tr>
                <tr style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 0.5rem 0; color: #8b949e;">Schema Migration Engine</td>
                    <td style="padding: 0.5rem 0; color: #f0f6fc; font-weight: 600;">Alembic 1.14</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem 0; color: #8b949e;">Financial Precision Model</td>
                    <td style="padding: 0.5rem 0; color: #10b981; font-weight: 600;">decimal.Decimal / Numeric(18, 2)</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
