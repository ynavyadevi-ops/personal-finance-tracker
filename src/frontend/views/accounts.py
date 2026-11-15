"""Accounts management view for creating, inspecting, and archiving financial accounts."""

from __future__ import annotations

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


def render_accounts_view() -> None:
    """Render financial accounts management interface."""
    render_header(
        title="Financial Accounts",
        subtitle="Create, inspect, and manage asset, liability, and depository accounts.",
        badge_text="Account Management",
        badge_type="accent",
    )

    tab_list, tab_create = st.tabs(["📋 Accounts Directory", "➕ Add New Account"])

    # =========================================================================
    # TAB 1: ACCOUNTS DIRECTORY
    # =========================================================================
    with tab_list:
        success, accounts = api_client.list_accounts(active_only=True)
        if success and accounts:
            for acc in accounts:
                acc_id = str(acc.get("id", ""))
                acc_name = acc.get("name", "Account")
                acc_type = acc.get("account_type", "CHECKING")
                institution = acc.get("institution_name") or "Self-managed"
                curr = acc.get("currency", "INR").upper()

                # Reconcile for live current balance
                rec_ok, rec_data = api_client.reconcile_account(acc_id)
                if rec_ok and "current_balance" in rec_data:
                    current_bal = Decimal(str(rec_data["current_balance"]))
                else:
                    current_bal = Decimal(str(acc.get("opening_balance", "0.00")))

                opening_bal = Decimal(str(acc.get("opening_balance", "0.00")))

                with st.container():
                    st.markdown(
                        f"""
                        <div class="fintech-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                                        <h4 style="margin: 0; color: {PALETTE["text"]};">{acc_name}</h4>
                                        {render_badge(acc_type, "accent")}
                                        {render_badge(curr, "secondary")}
                                    </div>
                                    <span style="color: {PALETTE["text_secondary"]}; font-size: 0.85rem;">
                                        Institution: {institution} • Opening: {format_money(opening_bal, curr)}
                                    </span>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 1.35rem; font-weight: 700; color: {PALETTE["positive"]};">
                                        {format_money(current_bal, curr)}
                                    </div>
                                    <span style="font-size: 0.75rem; color: {PALETTE["text_secondary"]};">Current Balance</span>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Actions expander for Editing metadata or Archiving
                    col_edit, col_arch = st.columns([1, 1])

                    with col_edit:
                        with st.expander(f"✏️ Edit Metadata: {acc_name}"):
                            with st.form(f"edit_acc_{acc_id}"):
                                new_name = st.text_input("Account Name", value=acc_name).strip()
                                new_inst = st.text_input(
                                    "Institution Name",
                                    value=acc.get("institution_name") or "",
                                ).strip()

                                update_btn = st.form_submit_button("Update Account Metadata")
                                if update_btn:
                                    if not new_name:
                                        st.error("Account Name cannot be empty.")
                                    else:
                                        up_ok, up_data = api_client.update_account(
                                            account_id=acc_id,
                                            payload={
                                                "name": new_name,
                                                "institution_name": new_inst if new_inst else None,
                                            },
                                        )
                                        if up_ok:
                                            st.success(
                                                f"Updated account '{new_name}' successfully."
                                            )
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to update: {up_data.get('message')}")

                    with col_arch:
                        with st.expander(f"⚠️ Archive Account: {acc_name}"):
                            st.write(
                                f"Archiving **{acc_name}** will hide it from active dropdowns. "
                                "Historical ledger transactions are preserved."
                            )
                            confirm_check = st.checkbox(
                                "I confirm I want to archive this account",
                                key=f"confirm_arch_{acc_id}",
                            )
                            if st.button("Confirm & Archive Account", key=f"btn_arch_{acc_id}"):
                                if confirm_check:
                                    arch_ok, arch_data = api_client.archive_account(acc_id)
                                    if arch_ok:
                                        st.success(f"Archived account '{acc_name}'.")
                                        st.rerun()
                                    else:
                                        st.error(f"Archive failed: {arch_data.get('message')}")
                                else:
                                    st.warning(
                                        "Please check the confirmation box before archiving."
                                    )

                    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

        else:
            render_empty_state(
                title="No Active Accounts",
                message="Switch to the 'Add New Account' tab to create your first financial account.",
                icon="🏦",
            )

    # =========================================================================
    # TAB 2: ADD NEW ACCOUNT
    # =========================================================================
    with tab_create:
        with st.form("create_account_form", clear_on_submit=True):
            st.markdown(
                f"<h4 style='color: {PALETTE['text']}; margin-bottom: 1rem;'>Register a Financial Account</h4>",
                unsafe_allow_html=True,
            )

            col_name, col_type = st.columns(2)
            with col_name:
                acc_name = st.text_input(
                    "Account Name*", placeholder="e.g. HDFC Salary Checking"
                ).strip()
            with col_type:
                acc_type = st.selectbox(
                    "Account Type*",
                    ["CHECKING", "SAVINGS", "CREDIT_CARD", "CASH", "INVESTMENT", "LOAN"],
                )

            col_inst, col_curr, col_bal = st.columns([2, 1, 2])
            with col_inst:
                acc_inst = st.text_input(
                    "Institution Name", placeholder="e.g. HDFC Bank, SBI, ICICI"
                ).strip()
            with col_curr:
                acc_curr = st.selectbox("Currency*", ["INR", "USD", "EUR", "GBP"], index=0)
            with col_bal:
                acc_balance = st.text_input(
                    "Opening Balance*",
                    value="0.00",
                    help="Initial balance (stored as exact Decimal, protected from floating-point noise).",
                ).strip()

            submitted = st.form_submit_button("Create Financial Account")
            if submitted:
                if not acc_name:
                    st.error("Account Name is required.")
                else:
                    try:
                        dec_balance = Decimal(acc_balance)
                    except Exception:
                        st.error("Opening balance must be a valid numerical amount.")
                        return

                    payload = {
                        "name": acc_name,
                        "account_type": acc_type,
                        "institution_name": acc_inst if acc_inst else None,
                        "currency": acc_curr,
                        "opening_balance": str(dec_balance),
                    }
                    create_ok, result = api_client.create_account(payload)
                    if create_ok:
                        st.success(f"Successfully created account '{acc_name}'.")
                        st.rerun()
                    else:
                        st.error(f"Failed to create account: {result.get('message')}")
