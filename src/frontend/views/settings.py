"""Settings view displaying authenticated profile and system configuration."""

from __future__ import annotations

import json
from datetime import date

import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.ui import PALETTE, render_badge, render_header


def render_settings_view() -> None:
    """Render profile details, currency preference, and runtime metadata."""
    render_header(
        title="Settings & Profile",
        subtitle="Review authenticated account credentials, currency preferences, and runtime metadata.",
        badge_text="Account Settings",
        badge_type="accent",
    )

    # 1. User Profile Section
    user_prof = st.session_state.get("user_profile") or {}
    if not user_prof.get("id"):
        prof_ok, fetched_prof = api_client.get_current_user()
        if prof_ok:
            user_prof = fetched_prof
            st.session_state["user_profile"] = user_prof

    user_name = user_prof.get("name", "Authenticated User")
    user_email = user_prof.get("email", "user@local.dev")
    user_id = user_prof.get("id", "Unknown")
    created_at = user_prof.get("created_at", "—")

    st.markdown(
        f"""
        <div class="fintech-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <h3 style="margin: 0; color: {PALETTE["text"]};">{user_name}</h3>
                    <span style="color: {PALETTE["accent"]}; font-size: 0.9rem;">{user_email}</span>
                </div>
                <div>
                    {render_badge("Active Session", "positive")}
                </div>
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 0.5rem 0; color: {PALETTE["text_secondary"]}; width: 35%;">User ID</td>
                    <td style="padding: 0.5rem 0; color: {PALETTE["text"]}; font-family: monospace;">{user_id}</td>
                </tr>
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 0.5rem 0; color: {PALETTE["text_secondary"]};">Account Created</td>
                    <td style="padding: 0.5rem 0; color: {PALETTE["text"]};">{created_at}</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem 0; color: {PALETTE["text_secondary"]};">Default Currency</td>
                    <td style="padding: 0.5rem 0; color: {PALETTE["positive"]}; font-weight: 600;">
                        INR (₹) — Indian Rupee (Default Core Currency)
                    </td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. System Runtime Information
    st.markdown(
        f"""
        <div class="fintech-card">
            <h4 style="margin-top: 0; color: {PALETTE["text"]};">System & Security Architecture</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 0.5rem 0; color: {PALETTE["text_secondary"]}; width: 35%;">Application</td>
                    <td style="padding: 0.5rem 0; color: {PALETTE["text"]}; font-weight: 600;">Personal Finance Tracker (Python + SQL)</td>
                </tr>
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 0.5rem 0; color: {PALETTE["text_secondary"]};">Frontend Engine</td>
                    <td style="padding: 0.5rem 0; color: {PALETTE["text"]};">Streamlit 1.41+ (Phase 5 Core UI)</td>
                </tr>
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 0.5rem 0; color: {PALETTE["text_secondary"]};">Backend API</td>
                    <td style="padding: 0.5rem 0; color: {PALETTE["text"]};">FastAPI 0.115+ (REST API v1)</td>
                </tr>
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 0.5rem 0; color: {PALETTE["text_secondary"]};">Authentication Mode</td>
                    <td style="padding: 0.5rem 0; color: {PALETTE["accent"]}; font-weight: 600;">
                        OAuth2 Password Bearer (Argon2id + Signed JWT HS256)
                    </td>
                </tr>
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 0.5rem 0; color: {PALETTE["text_secondary"]};">Persistence Layer</td>
                    <td style="padding: 0.5rem 0; color: {PALETTE["text"]};">SQLAlchemy 2.0 ORM + SQLite Foreign Keys</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem 0; color: {PALETTE["text_secondary"]};">Financial Math</td>
                    <td style="padding: 0.5rem 0; color: {PALETTE["positive"]}; font-weight: 600;">
                        Exact decimal.Decimal / Numeric(18, 2)
                    </td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Data Portability & Audit Exports
    with st.container():
        st.markdown(
            f"""
            <div class="fintech-card">
                <h4 style="margin-top: 0; color: {PALETTE["text"]};">Data Portability & Backup Archives</h4>
                <p style="color: {PALETTE["text_secondary"]}; font-size: 0.9rem; margin-bottom: 0.5rem;">
                    Download your user-scoped financial ledger records and complete backup snapshots in standard formats. Exports strictly exclude authentication secrets and protect against formula injection.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_exp1, col_exp2, col_exp3 = st.columns(3)
        today_str = date.today().isoformat()

        with col_exp1:
            st.markdown("##### 📄 CSV Export")
            st.caption("RFC 4180 tabular transaction records with formula injection mitigation.")
            if st.button("Generate CSV", key="btn_gen_csv", use_container_width=True):
                with st.spinner("Compiling CSV ledger..."):
                    ok, res = api_client.export_transactions_csv()
                    if ok and isinstance(res, str):
                        st.session_state["export_csv_data"] = res
                        st.success("CSV compiled!")
                    else:
                        msg = (
                            res.get("message", "Failed to compile CSV.")
                            if isinstance(res, dict)
                            else "Export failed."
                        )
                        st.error(msg)

            if st.session_state.get("export_csv_data"):
                st.download_button(
                    label="⬇️ Download CSV File",
                    data=st.session_state["export_csv_data"],
                    file_name=f"transactions_export_{today_str}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_csv_file",
                )

        with col_exp2:
            st.markdown("##### 📊 Excel (XLSX)")
            st.caption("Formatted binary spreadsheet workbook compatible with Excel & Calc.")
            if st.button("Generate Excel", key="btn_gen_xlsx", use_container_width=True):
                with st.spinner("Compiling Excel workbook..."):
                    ok, res_xlsx = api_client.export_transactions_xlsx()
                    if ok and isinstance(res_xlsx, bytes):
                        st.session_state["export_xlsx_data"] = res_xlsx
                        st.success("Excel compiled!")
                    else:
                        msg = (
                            res_xlsx.get("message", "Failed to compile Excel.")
                            if isinstance(res_xlsx, dict)
                            else "Export failed."
                        )
                        st.error(msg)

            if st.session_state.get("export_xlsx_data"):
                st.download_button(
                    label="⬇️ Download Excel File",
                    data=st.session_state["export_xlsx_data"],
                    file_name=f"transactions_export_{today_str}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_xlsx_file",
                )

        with col_exp3:
            st.markdown("##### 💾 JSON Backup")
            st.caption("Complete user-scoped JSON snapshot archiving all 9 domain entities.")
            if st.button("Generate Backup", key="btn_gen_json", use_container_width=True):
                with st.spinner("Preparing JSON backup..."):
                    ok, res_backup = api_client.get_user_backup()
                    if ok and isinstance(res_backup, dict):
                        st.session_state["export_json_data"] = json.dumps(res_backup, indent=2)
                        st.success("Backup compiled!")
                    else:
                        msg = (
                            res_backup.get("message", "Failed to compile backup.")
                            if isinstance(res_backup, dict)
                            else "Backup failed."
                        )
                        st.error(msg)

            if st.session_state.get("export_json_data"):
                st.download_button(
                    label="⬇️ Download Backup File",
                    data=st.session_state["export_json_data"],
                    file_name=f"user_backup_{today_str}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_json_file",
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Session Sign Out
    with st.container():
        st.markdown(
            f"<h4 style='color: {PALETTE['text']}; margin-bottom: 0.5rem;'>Sign Out</h4>",
            unsafe_allow_html=True,
        )
        st.write("End your authenticated browser session and revoke local client authorization.")
        if st.button("Log Out of FinanceTracker", type="primary"):
            st.session_state["access_token"] = None
            st.session_state["user_profile"] = None
            st.session_state["session_expired"] = False
            st.session_state["auth_error"] = None
            api_client.token = None
            st.rerun()
