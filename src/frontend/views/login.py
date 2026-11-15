"""Login view for user authentication."""

from __future__ import annotations

import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.ui import PALETTE


def render_login_view() -> None:
    """Render the dark fintech login portal and handle credential verification."""
    st.markdown("<br><br>", unsafe_allow_html=True)
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

        with st.form("login_form", clear_on_submit=False):
            st.markdown(
                f"<h4 style='margin-bottom: 1rem; color: {PALETTE['text']};'>Sign In to Your Account</h4>",
                unsafe_allow_html=True,
            )
            email = st.text_input("Email Address", placeholder="user@local.dev").strip()
            password = st.text_input("Password", type="password", placeholder="••••••••")

            submitted = st.form_submit_button("Authenticate & Enter", use_container_width=True)

            if submitted:
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
                        api_client.token = access_token

                        # Fetch and cache authenticated profile
                        prof_ok, profile = api_client.get_current_user()
                        if prof_ok:
                            st.session_state["user_profile"] = profile
                        else:
                            st.session_state["user_profile"] = {
                                "email": email,
                                "name": email.split("@")[0],
                            }

                        st.rerun()
                    else:
                        err_msg = result.get("message", "Invalid email or password.")
                        st.session_state["auth_error"] = err_msg
                        st.rerun()

        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 1.5rem; font-size: 0.85rem; color: {PALETTE["text_secondary"]};">
                Initial password setup for legacy accounts is managed via the local administrative terminal:<br>
                <code style="background-color: {PALETTE["surface_elevated"]}; color: {PALETTE["accent"]}; padding: 0.2rem 0.4rem; border-radius: 4px;">
                    python -m src.cli.enroll --email user@local.dev
                </code>
            </div>
            """,
            unsafe_allow_html=True,
        )
