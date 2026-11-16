"""Login and registration view for user authentication."""

from __future__ import annotations

import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.ui import PALETTE


def render_login_view() -> None:
    """Render the dark fintech authentication portal with Sign In and Sign Up tabs."""
    st.markdown("<br>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 1.8, 1])

    with col_center:
        st.markdown(
            f"""
            <div class="fintech-card" style="text-align: center; padding: 2rem 1.5rem; margin-bottom: 1.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💸</div>
                <h2 style="margin: 0; color: {PALETTE["text"]}; font-weight: 700;">FinanceTracker</h2>
                <p style="color: {PALETTE["text_secondary"]}; font-size: 0.95rem; margin-top: 0.25rem;">
                    Secure Double-Entry Personal Finance Platform
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("session_expired"):
            st.warning("⚠️ Your session has expired. Please log in again to continue.")

        auth_error = st.session_state.get("auth_error")
        if auth_error:
            st.error(f"❌ {auth_error}")

        auth_success = st.session_state.get("auth_success")
        if auth_success:
            st.success(f"✅ {auth_success}")

        tab_signin, tab_signup = st.tabs(["🔐 Sign In", "📝 Create Account"])

        # =====================================================================
        # SIGN IN TAB
        # =====================================================================
        with tab_signin:
            with st.form("login_form", clear_on_submit=False):
                st.markdown(
                    f"<h4 style='margin-bottom: 1rem; color: {PALETTE['text']};'>Sign In to Your Account</h4>",
                    unsafe_allow_html=True,
                )
                email = st.text_input(
                    "Email Address", placeholder="user@local.dev", key="signin_email"
                ).strip()
                password = st.text_input(
                    "Password", type="password", placeholder="••••••••", key="signin_password"
                )

                submitted = st.form_submit_button("Authenticate & Enter", use_container_width=True)

                if submitted:
                    st.session_state["auth_success"] = None
                    if not email or not password:
                        st.session_state["auth_error"] = "Please provide both email and password."
                        st.rerun()
                    else:
                        success, result = api_client.login(username=email, password=password)
                        if success:
                            access_token = result.get("access_token")
                            st.session_state["access_token"] = access_token
                            st.session_state["session_expired"] = False
                            st.session_state["auth_error"] = None
                            st.session_state["auth_success"] = None
                            api_client.token = access_token

                            # Fetch and cache authenticated profile
                            prof_ok, profile = api_client.get_current_user()
                            if prof_ok:
                                st.session_state["user_profile"] = profile
                            else:
                                st.session_state["user_profile"] = {
                                    "email": email,
                                    "name": email.split("@")[0],
                                    "role": result.get("role", "USER"),
                                    "must_change_password": result.get(
                                        "must_change_password", False
                                    ),
                                }

                            st.rerun()
                        else:
                            err_msg = result.get("message", "Invalid email or password.")
                            st.session_state["auth_error"] = err_msg
                            st.rerun()

        # =====================================================================
        # CREATE ACCOUNT TAB
        # =====================================================================
        with tab_signup:
            with st.form("register_form", clear_on_submit=False):
                st.markdown(
                    f"<h4 style='margin-bottom: 1rem; color: {PALETTE['text']};'>Create New Account</h4>",
                    unsafe_allow_html=True,
                )
                reg_name = st.text_input(
                    "Full Name", placeholder="e.g. Jane Doe", key="signup_name"
                ).strip()
                reg_email = st.text_input(
                    "Email Address", placeholder="e.g. jane@example.com", key="signup_email"
                ).strip()
                reg_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="••••••••",
                    help="Min 8 characters, at least 1 uppercase, 1 lowercase, 1 digit, and 1 special character.",
                    key="signup_password",
                )
                reg_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="••••••••",
                    key="signup_confirm",
                )

                st.markdown(
                    f"""
                    <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]}; margin-bottom: 1rem;">
                        Password requirements: Minimum 8 characters with at least one uppercase letter, one lowercase letter, one number, and one symbol.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

                if reg_submitted:
                    st.session_state["auth_error"] = None
                    if not reg_name or not reg_email or not reg_password or not reg_confirm:
                        st.session_state["auth_error"] = "All registration fields are required."
                        st.rerun()
                    elif reg_password != reg_confirm:
                        st.session_state["auth_error"] = "Passwords do not match."
                        st.rerun()
                    else:
                        reg_ok, reg_result = api_client.register(
                            name=reg_name,
                            email=reg_email,
                            password=reg_password,
                            confirm_password=reg_confirm,
                        )
                        if reg_ok:
                            st.session_state["auth_error"] = None
                            st.session_state["auth_success"] = (
                                f"Account created successfully for {reg_email}! Please sign in using your credentials."
                            )
                            st.rerun()
                        else:
                            st.session_state["auth_error"] = reg_result.get(
                                "message", "Unable to complete registration."
                            )
                            st.rerun()

        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 1.5rem; font-size: 0.85rem; color: {PALETTE["text_secondary"]};">
                Administrator bootstrap and legacy account password setup via local terminal:<br>
                <code style="background-color: {PALETTE["surface_elevated"]}; color: {PALETTE["accent"]}; padding: 0.2rem 0.4rem; border-radius: 4px;">
                    python -m src.cli.bootstrap_admin --email admin@local.dev
                </code>
            </div>
            """,
            unsafe_allow_html=True,
        )
