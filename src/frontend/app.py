"""Streamlit interactive web dashboard for Personal Finance Tracker."""

from __future__ import annotations

import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.ui import PALETTE, apply_custom_css
from src.frontend.views import (
    render_accounts_view,
    render_analytics_view,
    render_budgets_view,
    render_dashboard_view,
    render_goals_view,
    render_investments_view,
    render_loans_view,
    render_login_view,
    render_recurring_view,
    render_settings_view,
    render_transactions_view,
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

# ==============================================================================
# AUTHENTICATION BARRIER
# ==============================================================================
access_token = st.session_state.get("access_token")
if not access_token:
    api_client.token = None
    render_login_view()
    st.stop()

# Synchronize API client bearer token
api_client.token = access_token

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
st.sidebar.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
        <span style="font-size: 1.75rem;">💸</span>
        <div>
            <span style="font-size: 1.15rem; font-weight: 700; color: {PALETTE["text"]};">FinanceTracker</span>
            <div style="font-size: 0.75rem; color: {PALETTE["accent"]}; font-weight: 600;">Phase 7 Analytics & AI</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Display authenticated user identity badge
user_profile = st.session_state.get("user_profile") or {}
user_email = user_profile.get("email", "Authenticated")
st.sidebar.markdown(
    f"""
    <div style="background-color: {PALETTE["surface_elevated"]}; border-radius: 6px; padding: 0.6rem 0.8rem; margin-bottom: 1rem; border: 1px solid {PALETTE["border"]};">
        <div style="font-size: 0.75rem; color: {PALETTE["text_secondary"]}; text-transform: uppercase; font-weight: 600;">Signed in as</div>
        <div style="font-size: 0.85rem; color: {PALETTE["text"]}; font-weight: 600; text-overflow: ellipsis; overflow: hidden;">{user_email}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

NAV_OPTIONS = [
    "📊 Dashboard",
    "📈 Analytics & Insights",
    "🏦 Accounts",
    "💳 Transactions",
    "🎯 Budgets",
    "🏆 Savings Goals",
    "📉 Loans & Debts",
    "📈 Investments",
    "🔄 Recurring Rules",
    "⚙️ Settings",
]

selected_nav = st.sidebar.radio(
    "Navigation",
    NAV_OPTIONS,
    index=0,
    label_visibility="collapsed",
)

# Sidebar System Health Probe
st.sidebar.markdown("<hr style='border-color: #334155; margin: 1rem 0;'>", unsafe_allow_html=True)
is_healthy, health_data = api_client.check_health()
if is_healthy:
    st.sidebar.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: {PALETTE["positive"]};">
            <span style="height: 8px; width: 8px; background-color: {PALETTE["positive"]}; border-radius: 50%; display: inline-block;"></span>
            <span>FastAPI: Connected</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    err_text = health_data.get("message", "Offline")
    st.sidebar.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: {PALETTE["negative"]};">
            <span style="height: 8px; width: 8px; background-color: {PALETTE["negative"]}; border-radius: 50%; display: inline-block;"></span>
            <span>FastAPI: {err_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Sidebar Logout Button
st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("Log Out", key="sidebar_logout_btn", use_container_width=True):
    st.session_state["access_token"] = None
    st.session_state["user_profile"] = None
    st.session_state["session_expired"] = False
    st.session_state["auth_error"] = None
    api_client.token = None
    st.rerun()

st.sidebar.caption("Personal Finance Tracker • Phase 7")

# ==============================================================================
# ROUTING CONTROLLER
# ==============================================================================
if selected_nav == "📊 Dashboard":
    render_dashboard_view()
elif selected_nav == "📈 Analytics & Insights":
    render_analytics_view()
elif selected_nav == "🏦 Accounts":
    render_accounts_view()
elif selected_nav == "💳 Transactions":
    render_transactions_view()
elif selected_nav == "🎯 Budgets":
    render_budgets_view()
elif selected_nav == "🏆 Savings Goals":
    render_goals_view()
elif selected_nav == "📉 Loans & Debts":
    render_loans_view()
elif selected_nav == "📈 Investments":
    render_investments_view()
elif selected_nav == "🔄 Recurring Rules":
    render_recurring_view()
elif selected_nav == "⚙️ Settings":
    render_settings_view()
