"""Administrative Portal view providing system metrics, user governance, and audit trails."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.ui import PALETTE, render_header


def render_admin_view() -> None:
    """Render administrative portal dashboard.

    Strictly enforces:
    - Visibility limited to users with ADMIN role.
    - Zero exposure of financial transactions, balances, or user-private data.
    - User management (search, enable/disable status toggle, temporary password reset).
    - Immutable audit log inspection.
    - Platform configuration (registration kill-switch).
    """
    # Double-check client-side role authorization
    profile = st.session_state.get("user_profile") or {}
    if profile.get("role") != "ADMIN":
        st.error("⛔ Access Denied. Administrative privileges required to access this portal.")
        st.stop()

    render_header(
        title="Administrative Portal",
        subtitle="System governance, user lifecycle management, and security audit monitoring.",
        badge_text="Administrator",
        badge_type="accent",
    )

    tab_overview, tab_users, tab_audit, tab_settings = st.tabs(
        ["📊 Platform Overview", "👥 User Management", "🛡️ Security & Audit", "⚙️ System Settings"]
    )

    # =========================================================================
    # TAB 1: PLATFORM OVERVIEW
    # =========================================================================
    with tab_overview:
        st.markdown(
            f"<h3 style='color: {PALETTE['text']};'>System Health & Overview</h3>",
            unsafe_allow_html=True,
        )

        ok, overview_data = api_client.get_admin_overview()
        if not ok or not overview_data:
            st.error("Failed to load platform overview metrics.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    label="Total Registered Users",
                    value=str(overview_data.get("total_users", 0)),
                    delta="User Base",
                )
            with col2:
                active_cnt = overview_data.get("active_users", 0)
                disabled_cnt = overview_data.get("disabled_users", 0)
                st.metric(
                    label="Active / Disabled Users",
                    value=f"{active_cnt} / {disabled_cnt}",
                    delta=f"{disabled_cnt} Disabled" if disabled_cnt > 0 else "All Active",
                    delta_color="inverse" if disabled_cnt > 0 else "normal",
                )
            with col3:
                st.metric(
                    label="New Registrations (30d)",
                    value=str(overview_data.get("recent_registrations_30d", 0)),
                    delta="Last 30 Days",
                )
            with col4:
                reg_status = "Enabled" if overview_data.get("registration_enabled") else "Disabled"
                st.metric(
                    label="Public Registration",
                    value=reg_status,
                    delta="Kill-Switch",
                    delta_color="normal" if reg_status == "Enabled" else "inverse",
                )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="fintech-card">
                    <h4 style="margin-top: 0; color: {PALETTE["text"]};">Security & Data Privacy Boundary</h4>
                    <p style="color: {PALETTE["text_secondary"]}; font-size: 0.9rem; line-height: 1.5;">
                        🛡️ <strong>Zero Financial Exposure:</strong> Administrator accounts are strictly segregated from customer financial records.
                        Financial accounts, transaction entries, budget limits, loan records, and investment holdings cannot be queried or viewed
                        through administrative interfaces. All user governance operations are immutably logged to the audit repository.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # =========================================================================
    # TAB 2: USER MANAGEMENT
    # =========================================================================
    with tab_users:
        st.markdown(
            f"<h3 style='color: {PALETTE['text']};'>User Governance</h3>", unsafe_allow_html=True
        )

        # Filters
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        with f_col1:
            search_query = st.text_input(
                "Search by Name or Email", placeholder="e.g. user@local.dev"
            ).strip()
        with f_col2:
            role_filter = st.selectbox("Role Filter", ["All", "USER", "ADMIN"])
        with f_col3:
            status_filter = st.selectbox("Status Filter", ["All", "Active Only", "Disabled Only"])

        api_role = None if role_filter == "All" else role_filter
        api_active = None
        if status_filter == "Active Only":
            api_active = True
        elif status_filter == "Disabled Only":
            api_active = False

        u_ok, users_list = api_client.list_admin_users(
            search=search_query or None,
            role=api_role,
            active_only=api_active,
            page=1,
            page_size=100,
        )

        if not u_ok:
            st.error("Failed to retrieve user accounts.")
        elif not users_list:
            st.info("No registered users match the search criteria.")
        else:
            table_rows = []
            for u in users_list:
                table_rows.append(
                    {
                        "ID": u["id"][:8] + "...",
                        "Full ID": u["id"],
                        "Name": u.get("name") or "—",
                        "Email": u.get("email") or "—",
                        "Role": u.get("role") or "USER",
                        "Status": "Active" if u.get("is_active") else "Disabled",
                        "Must Change Password": "Yes" if u.get("must_change_password") else "No",
                        "Created At": str(u.get("created_at") or "")[:19] or "—",
                    }
                )

            df_display = pd.DataFrame(
                [
                    {
                        "ID": r["ID"],
                        "Name": r["Name"],
                        "Email": r["Email"],
                        "Role": r["Role"],
                        "Status": r["Status"],
                        "Password Change Required": r["Must Change Password"],
                        "Created Date": r["Created At"],
                    }
                    for r in table_rows
                ]
            )
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown(
                f"<h4 style='color: {PALETTE['text']};'>User Actions</h4>", unsafe_allow_html=True
            )

            action_user = st.selectbox(
                "Select Target User",
                options=users_list,
                format_func=lambda u: f"{u.get('name')} ({u.get('email')}) — [{u.get('role')}, {'Active' if u.get('is_active') else 'Disabled'}]",
                key="admin_target_user_select",
            )

            if action_user:
                current_admin_id = profile.get("id")
                is_self = action_user.get("id") == current_admin_id

                col_status, col_reset = st.columns(2)

                # Status toggle
                with col_status:
                    st.markdown(
                        f"""
                        <div class="fintech-card">
                            <h5 style="margin-top: 0; color: {PALETTE["text"]};">Account Status</h5>
                            <p style="font-size: 0.85rem; color: {PALETTE["text_secondary"]};">
                                Currently: <strong>{"Active" if action_user.get("is_active") else "Disabled"}</strong>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if is_self:
                        st.caption("⚠️ You cannot disable your own administrator account.")
                    else:
                        new_status = not action_user.get("is_active")
                        btn_label = (
                            "Deactivate Account"
                            if action_user.get("is_active")
                            else "Activate Account"
                        )

                        if st.button(btn_label, key=f"btn_toggle_status_{action_user['id']}"):
                            succ, resp = api_client.update_user_status(
                                action_user["id"], new_status
                            )
                            if succ:
                                st.success(
                                    f"User account status updated to {'Active' if new_status else 'Disabled'}."
                                )
                                st.rerun()
                            else:
                                st.error(f"Failed to update status: {resp.get('message')}")

                # Password Reset
                with col_reset:
                    st.markdown(
                        f"""
                        <div class="fintech-card">
                            <h5 style="margin-top: 0; color: {PALETTE["text"]};">Administrative Password Reset</h5>
                            <p style="font-size: 0.85rem; color: {PALETTE["text_secondary"]};">
                                Generates a secure temporary password and flags account for mandatory change on next login.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Generate Temporary Password", key=f"btn_reset_pwd_{action_user['id']}"
                    ):
                        succ, resp = api_client.admin_reset_user_password(action_user["id"])
                        if succ:
                            temp_pwd = resp.get("temporary_password")
                            st.session_state[f"temp_pwd_generated_{action_user['id']}"] = temp_pwd
                            st.success("Temporary password generated successfully!")
                        else:
                            st.error(f"Failed to reset password: {resp.get('message')}")

                    temp_shown = st.session_state.get(f"temp_pwd_generated_{action_user['id']}")
                    if temp_shown:
                        st.markdown(
                            f"""
                            <div style="background-color: rgba(245, 158, 11, 0.15); border: 1px solid {PALETTE["warning"]}; border-radius: 6px; padding: 1rem; margin-top: 0.5rem;">
                                <div style="color: {PALETTE["warning"]}; font-weight: 700; margin-bottom: 0.25rem;">⚠️ ONE-TIME TEMPORARY PASSWORD:</div>
                                <code style="font-size: 1.1rem; color: {PALETTE["text"]}; background-color: #0F172A; padding: 0.3rem 0.6rem; border-radius: 4px; display: inline-block;">{temp_shown}</code>
                                <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]}; margin-top: 0.5rem;">
                                    Provide this securely to the user. It will not be stored in plain text or shown again.
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    # =========================================================================
    # TAB 3: SECURITY & AUDIT
    # =========================================================================
    with tab_audit:
        st.markdown(
            f"<h3 style='color: {PALETTE['text']};'>Security & Administrative Audit Log</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='color: {PALETTE['text_secondary']}; font-size: 0.9rem;'>Review immutable security events and governance actions.</p>",
            unsafe_allow_html=True,
        )

        limit = st.slider(
            "Audit entries to display", min_value=10, max_value=100, value=50, step=10
        )
        a_ok, audit_logs = api_client.get_admin_audit_logs(limit=limit)

        if not a_ok:
            st.error("Failed to fetch audit log trail.")
        elif not audit_logs:
            st.info("No administrative audit entries found.")
        else:
            log_entries = []
            for entry in audit_logs:
                log_entries.append(
                    {
                        "Timestamp": str(entry.get("created_at") or "")[:19] or "—",
                        "Action": entry.get("action", "—"),
                        "Entity": entry.get("entity_name", "—"),
                        "Actor Admin ID": str(entry.get("user_id") or "")[:8] + "...",
                        "Target Entity ID": str(entry.get("entity_id") or "")[:8] + "...",
                        "IP Address": entry.get("ip_address") or "local",
                        "New Values": entry.get("new_values") or "—",
                    }
                )
            df_audit = pd.DataFrame(log_entries)
            st.dataframe(df_audit, use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 4: SYSTEM SETTINGS
    # =========================================================================
    with tab_settings:
        st.markdown(
            f"<h3 style='color: {PALETTE['text']};'>Platform Configuration</h3>",
            unsafe_allow_html=True,
        )

        s_ok, settings_data = api_client.get_admin_settings()
        reg_enabled_current = True
        if s_ok and settings_data:
            for s in settings_data:
                if s.get("key") == "registration_enabled":
                    reg_enabled_current = str(s.get("value")).lower() == "true"

        st.markdown(
            f"""
            <div class="fintech-card">
                <h4 style="margin-top: 0; color: {PALETTE["text"]};">Public Registration Kill-Switch</h4>
                <p style="color: {PALETTE["text_secondary"]}; font-size: 0.9rem;">
                    When enabled, visitors can create new user accounts via the Sign Up form on the login screen.<br>
                    When disabled, the registration endpoint immediately rejects all new registrations with HTTP 403 Forbidden.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("settings_registration_form"):
            new_reg_setting = st.toggle(
                "Allow Public User Registration",
                value=reg_enabled_current,
                help="Toggle whether public users may register new accounts.",
            )
            submitted_settings = st.form_submit_button("Save Platform Configuration")
            if submitted_settings:
                succ, res = api_client.update_admin_settings(registration_enabled=new_reg_setting)
                if succ:
                    st.success("Platform settings successfully updated!")
                    st.rerun()
                else:
                    st.error(f"Failed to update settings: {res.get('message')}")
