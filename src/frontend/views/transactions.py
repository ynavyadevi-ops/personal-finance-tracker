"""Transactions view for ledger tracking, income/expense recording, and transfers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components.ui import (
    PALETTE,
    format_money,
    render_badge,
    render_empty_state,
    render_header,
)


def render_transactions_view() -> None:
    """Render financial transactions ledger and recording forms."""
    render_header(
        title="Transaction Ledger",
        subtitle="Record income, expense, and balanced inter-account transfers with double-entry integrity.",
        badge_text="Double-Entry Core",
        badge_type="accent",
    )

    # Pre-fetch active accounts for account selection dropdowns
    acc_ok, accounts = api_client.list_accounts(active_only=True)
    if not acc_ok or not accounts:
        render_empty_state(
            title="Accounts Required",
            message="Please create at least one financial account before recording transactions.",
            icon="🏦",
        )
        return

    account_map = {acc["id"]: acc for acc in accounts}
    account_options = {acc["id"]: f"{acc['name']} ({acc['currency']})" for acc in accounts}

    tab_ledger, tab_record, tab_transfer = st.tabs(
        ["📜 Transaction Ledger", "➕ Record Income / Expense", "🔄 Inter-Account Transfer"]
    )

    # =========================================================================
    # TAB 1: TRANSACTION LEDGER
    # =========================================================================
    with tab_ledger:
        st.markdown(
            f"<h4 style='color: {PALETTE['text']}; margin-bottom: 0.75rem;'>Filter & Query Ledger</h4>",
            unsafe_allow_html=True,
        )

        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            selected_acc = st.selectbox(
                "Filter by Account",
                options=["ALL"] + list(account_options.keys()),
                format_func=lambda x: "All Accounts" if x == "ALL" else account_options.get(x, x),
            )
        with filter_col2:
            selected_type = st.selectbox(
                "Transaction Type",
                options=["ALL", "INCOME", "EXPENSE", "TRANSFER"],
            )
        with filter_col3:
            page_size = st.selectbox("Page Size", options=[10, 25, 50], index=1)

        # Pagination state
        page_num = st.number_input("Page", min_value=1, value=1, step=1)

        # Fetch matching transactions
        acc_param = None if selected_acc == "ALL" else selected_acc
        type_param = None if selected_type == "ALL" else selected_type

        tx_ok, tx_result = api_client.list_transactions(
            account_id=acc_param,
            transaction_type=type_param,
            page=page_num,
            page_size=page_size,
        )

        if tx_ok and isinstance(tx_result, dict):
            tx_items = tx_result.get("items", [])
            meta = tx_result.get("meta", {})
            total_items = meta.get("total", len(tx_items))
            total_pages = meta.get("pages", 1)

            st.caption(
                f"Showing page {page_num} of {total_pages} (Total: {total_items} transactions)"
            )

            if tx_items:
                for tx in tx_items:
                    tx_id = tx.get("id", "")
                    tx_date = tx.get("transaction_date")
                    desc = tx.get("description", "Transaction")
                    tx_type = tx.get("transaction_type", "EXPENSE")
                    curr = tx.get("currency", "INR")
                    amt = Decimal(str(tx.get("amount", "0.00")))
                    entries = tx.get("entries", [])

                    badge_color = (
                        "positive"
                        if tx_type == "INCOME"
                        else ("negative" if tx_type == "EXPENSE" else "accent")
                    )

                    with st.container():
                        st.markdown(
                            f"""
                            <div class="fintech-card" style="margin-bottom: 0.5rem; padding: 0.85rem 1.25rem;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                                            <span style="font-weight: 600; color: {PALETTE["text"]};">{desc}</span>
                                            {render_badge(tx_type, badge_color)}
                                        </div>
                                        <span style="color: {PALETTE["text_secondary"]}; font-size: 0.8rem;">
                                            Date: {tx_date} • Currency: {curr}
                                        </span>
                                    </div>
                                    <div style="text-align: right;">
                                        <span style="font-size: 1.15rem; font-weight: 700; color: {PALETTE[badge_color]};">
                                            {"+" if tx_type == "INCOME" else ("-" if tx_type == "EXPENSE" else "")}{format_money(amt, curr)}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Reversal and entries expander
                        with st.expander(f"🔍 Details & Reversal: {desc} ({tx_id[:8]})"):
                            st.write(f"**Transaction ID:** `{tx_id}`")
                            st.write(f"**Notes:** {tx.get('notes') or 'None'}")
                            st.write(f"**Tags:** {tx.get('tags') or 'None'}")

                            if entries:
                                st.write("**Double-Entry Ledger Lines:**")
                                entry_rows = []
                                for ent in entries:
                                    acc_id = ent.get("account_id")
                                    account_title = account_map.get(acc_id, {}).get("name", acc_id)
                                    entry_rows.append(
                                        {
                                            "Entry Type": ent.get("entry_type"),
                                            "Account": account_title,
                                            "Amount": format_money(ent.get("amount", "0.00"), curr),
                                        }
                                    )
                                st.dataframe(pd.DataFrame(entry_rows), hide_index=True)

                            st.markdown("---")
                            st.write("##### Compensating Reversal")
                            reversal_reason = st.text_input(
                                "Reversal Reason",
                                value="User requested reversal",
                                key=f"rev_reason_{tx_id}",
                            ).strip()
                            confirm_rev = st.checkbox(
                                "I confirm I want to reverse this transaction",
                                key=f"check_rev_{tx_id}",
                            )
                            if st.button("Reverse Transaction", key=f"btn_rev_{tx_id}"):
                                if confirm_rev:
                                    rev_ok, rev_res = api_client.reverse_transaction(
                                        transaction_id=tx_id, reason=reversal_reason
                                    )
                                    if rev_ok:
                                        st.success("Transaction reversed successfully.")
                                        st.rerun()
                                    else:
                                        st.error(f"Reversal failed: {rev_res.get('message')}")
                                else:
                                    st.warning("Please check the confirmation box.")

            else:
                render_empty_state(
                    title="No Matching Transactions",
                    message="No ledger records matched the specified filter criteria.",
                    icon="🔍",
                )
        else:
            st.error("Failed to fetch transactions from backend.")

    # =========================================================================
    # TAB 2: RECORD INCOME / EXPENSE
    # =========================================================================
    with tab_record:
        with st.form("record_tx_form", clear_on_submit=True):
            st.markdown(
                f"<h4 style='color: {PALETTE['text']}; margin-bottom: 1rem;'>Record Financial Transaction</h4>",
                unsafe_allow_html=True,
            )

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                tx_direction = st.selectbox("Transaction Type*", ["EXPENSE", "INCOME"])
            with col_t2:
                target_acc_id = st.selectbox(
                    "Target Account*",
                    options=list(account_options.keys()),
                    format_func=lambda x: account_options.get(x, x),
                )

            col_amt, col_date = st.columns([2, 1])
            with col_amt:
                amt_str = st.text_input("Amount*", placeholder="e.g. 1500.00").strip()
            with col_date:
                tx_date = st.date_input("Transaction Date*", value=date.today())

            tx_desc = st.text_input(
                "Description*", placeholder="e.g. Monthly Grocery Restock"
            ).strip()

            col_notes, col_tags = st.columns(2)
            with col_notes:
                notes = st.text_input(
                    "Notes (Optional)", placeholder="Store name, receipt number"
                ).strip()
            with col_tags:
                tags = st.text_input("Tags (Optional)", placeholder="groceries, essential").strip()

            submitted_tx = st.form_submit_button("Record Transaction")
            if submitted_tx:
                if not tx_desc:
                    st.error("Transaction description is required.")
                elif not amt_str:
                    st.error("Amount is required.")
                else:
                    try:
                        amt_dec = Decimal(amt_str)
                        if amt_dec <= Decimal("0.00"):
                            st.error("Amount must be strictly positive.")
                            return
                    except Exception:
                        st.error("Amount must be a valid numerical value.")
                        return

                    target_currency = account_map.get(target_acc_id, {}).get("currency", "INR")
                    payload = {
                        "account_id": target_acc_id,
                        "transaction_type": tx_direction,
                        "amount": str(amt_dec),
                        "description": tx_desc,
                        "transaction_date": tx_date.isoformat(),
                        "currency": target_currency,
                        "notes": notes if notes else None,
                        "tags": tags if tags else None,
                    }

                    c_ok, c_res = api_client.create_transaction(payload)
                    if c_ok:
                        st.success(
                            f"Recorded {tx_direction} of {format_money(amt_dec, target_currency)}."
                        )
                        st.rerun()
                    else:
                        st.error(f"Failed to record transaction: {c_res.get('message')}")

    # =========================================================================
    # TAB 3: INTER-ACCOUNT TRANSFER
    # =========================================================================
    with tab_transfer:
        with st.form("transfer_form", clear_on_submit=True):
            st.markdown(
                f"<h4 style='color: {PALETTE['text']}; margin-bottom: 1rem;'>Inter-Account Transfer</h4>",
                unsafe_allow_html=True,
            )

            col_src, col_dst = st.columns(2)
            with col_src:
                src_acc_id = st.selectbox(
                    "Source Account (Debit/Origin)*",
                    options=list(account_options.keys()),
                    format_func=lambda x: account_options.get(x, x),
                    key="src_acc_select",
                )
            with col_dst:
                dst_acc_id = st.selectbox(
                    "Destination Account (Credit/Target)*",
                    options=list(account_options.keys()),
                    format_func=lambda x: account_options.get(x, x),
                    key="dst_acc_select",
                )

            src_curr = account_map.get(src_acc_id, {}).get("currency", "INR")
            dst_curr = account_map.get(dst_acc_id, {}).get("currency", "INR")

            if src_curr != dst_curr:
                st.warning(
                    f"⚠️ Currency Mismatch: Source is **{src_curr}** and Destination is **{dst_curr}**. "
                    "Cross-currency transfers without an approved exchange rate are prohibited."
                )

            col_t_amt, col_t_date = st.columns([2, 1])
            with col_t_amt:
                t_amt_str = st.text_input("Transfer Amount*", placeholder="e.g. 5000.00").strip()
            with col_t_date:
                t_date = st.date_input("Transfer Date*", value=date.today(), key="transfer_date")

            t_desc = st.text_input("Description", value="Account Transfer").strip()

            submitted_transfer = st.form_submit_button("Execute Inter-Account Transfer")
            if submitted_transfer:
                if src_acc_id == dst_acc_id:
                    st.error("Source and Destination accounts must be distinct.")
                elif src_curr != dst_curr:
                    st.error(
                        f"Cannot transfer between different currencies ({src_curr} -> {dst_curr})."
                    )
                elif not t_amt_str:
                    st.error("Transfer amount is required.")
                else:
                    try:
                        amt_dec = Decimal(t_amt_str)
                        if amt_dec <= Decimal("0.00"):
                            st.error("Amount must be strictly positive.")
                            return
                    except Exception:
                        st.error("Transfer amount must be a valid numerical value.")
                        return

                    transfer_payload = {
                        "source_account_id": src_acc_id,
                        "destination_account_id": dst_acc_id,
                        "amount": str(amt_dec),
                        "currency": src_curr,
                        "description": t_desc,
                        "transaction_date": t_date.isoformat(),
                    }

                    tr_ok, tr_res = api_client.create_transfer(transfer_payload)
                    if tr_ok:
                        st.success(
                            f"Successfully transferred {format_money(amt_dec, src_curr)} "
                            f"from {account_map[src_acc_id]['name']} to {account_map[dst_acc_id]['name']}."
                        )
                        st.rerun()
                    else:
                        st.error(f"Transfer failed: {tr_res.get('message')}")
