"""Streamlit interactive web dashboard for Personal Finance Tracker."""

from __future__ import annotations

import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.ui import PALETTE, apply_custom_css
from src.frontend.views import (
    render_accounts_view,
    render_admin_view,
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

# Load or refresh authenticated profile if missing
user_profile = st.session_state.get("user_profile") or {}
if not user_profile.get("id"):
    prof_ok, fetched_prof = api_client.get_current_user()
    if prof_ok:
        user_profile = fetched_prof
        st.session_state["user_profile"] = user_profile

# ==============================================================================
# MANDATORY FIRST-LOGIN PASSWORD CHANGE BARRIER
# ==============================================================================
if user_profile.get("must_change_password"):
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.markdown(
            f"""
            <div class="fintech-card" style="border-color: {PALETTE["warning"]}; padding: 1.5rem;">
                <h3 style="color: {PALETTE["warning"]}; margin-top: 0;">⚠️ Mandatory Password Change</h3>
                <p style="color: {PALETTE["text_secondary"]}; font-size: 0.95rem; line-height: 1.5;">
                    Your account has been flagged for a mandatory password update.
                    Please choose a strong, new password before accessing the platform.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("mandatory_password_change_form"):
            curr_pass = st.text_input("Temporary / Current Password", type="password")
            new_pass = st.text_input(
                "New Password",
                type="password",
                help="Minimum 8 characters, uppercase, lowercase, number, symbol.",
            )
            conf_pass = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button(
                "Update Password & Continue", use_container_width=True
            )

            if submitted:
                if not curr_pass or not new_pass or not conf_pass:
                    st.error("All password fields are required.")
                elif new_pass != conf_pass:
                    st.error("New passwords do not match.")
                else:
                    succ, res = api_client.change_password(curr_pass, new_pass, conf_pass)
                    if succ:
                        st.success(
                            "Password changed successfully! Please sign in with your new password."
                        )
                        st.session_state["access_token"] = None
                        st.session_state["user_profile"] = None
                        st.session_state["auth_success"] = (
                            "Password updated successfully. Please log in."
                        )
                        st.rerun()
                    else:
                        st.error(f"Error: {res.get('message', 'Failed to update password.')}")

        if st.button("Log Out & Exit", key="force_pwd_logout"):
            st.session_state["access_token"] = None
            st.session_state["user_profile"] = None
            st.rerun()

    st.stop()

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
st.sidebar.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
        <span style="font-size: 1.75rem;">💸</span>
        <div>
            <span style="font-size: 1.15rem; font-weight: 700; color: {PALETTE["text"]};">FinanceTracker</span>
            <div style="font-size: 0.75rem; color: {PALETTE["accent"]}; font-weight: 600;">Personal Finance Platform</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Display authenticated user identity badge
user_email = user_profile.get("email", "Authenticated")
user_role = user_profile.get("role", "USER")
st.sidebar.markdown(
    f"""
    <div style="background-color: {PALETTE["surface_elevated"]}; border-radius: 6px; padding: 0.6rem 0.8rem; margin-bottom: 1rem; border: 1px solid {PALETTE["border"]};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.75rem; color: {PALETTE["text_secondary"]}; text-transform: uppercase; font-weight: 600;">Signed in as</span>
            <span style="font-size: 0.7rem; color: {PALETTE["accent"]}; background: rgba(56, 189, 248, 0.15); padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: 700;">{user_role}</span>
        </div>
        <div style="font-size: 0.85rem; color: {PALETTE["text"]}; font-weight: 600; text-overflow: ellipsis; overflow: hidden; margin-top: 0.2rem;">{user_email}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

nav_options = [
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
if user_role == "ADMIN":
    nav_options.append("🛡️ Admin Portal")

selected_nav = st.sidebar.radio(
    "Navigation",
    nav_options,
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

st.sidebar.caption("Personal Finance Tracker • Governance")

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
elif selected_nav == "🛡️ Admin Portal":
    if user_role == "ADMIN":
        render_admin_view()
    else:
        st.error("⛔ Access Denied. Administrative privileges required.")
