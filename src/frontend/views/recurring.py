"""Recurring transactions view for schedule management, pause/resume, and manual execution."""

from __future__ import annotations

from datetime import date
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


def render_recurring_view() -> None:
    """Render recurring transaction rule automation, due executions, and schedule controls."""
    render_header(
        title="Recurring Transaction Rules",
        subtitle="Configure automated recurring schedules and execute due periodic transactions into the double-entry ledger.",
        badge_text="Automation",
        badge_type="accent",
    )

    tab_rules, tab_create = st.tabs(
        ["🔄 Scheduled Rules & Due Executions", "➕ Create Recurring Rule"]
    )

    # =========================================================================
    # TAB 1: RULES DIRECTORY & DUE EXECUTIONS
    # =========================================================================
    with tab_rules:
        # 1. Check for due recurring rules awaiting execution
        due_ok, due_rules = api_client.list_due_recurring_rules()

        if due_ok and due_rules:
            st.markdown(
                f"""
                <div style="background-color: rgba(245, 158, 11, 0.1); border: 1px solid {PALETTE["warning"]}; border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem;">
                    <div style="font-size: 1.05rem; font-weight: 700; color: {PALETTE["warning"]}; margin-bottom: 0.25rem;">
                        ⚡ {len(due_rules)} Rule(s) Due for Execution
                    </div>
                    <div style="font-size: 0.85rem; color: {PALETTE["text_secondary"]};">
                        The following recurring transactions have reached their scheduled milestone. In compliance with architectural specifications, executions must be explicitly triggered to create double-entry ledger postings.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for due_rule in due_rules:
                d_id = due_rule.get("id", "")
                d_name = due_rule.get("name", "Recurring Schedule")
                d_amt = Decimal(str(due_rule.get("amount", "0.00")))
                d_curr = due_rule.get("currency", "INR")
                d_due = due_rule.get("next_occurrence", "")

                with st.container():
                    st.markdown(
                        f"""
                        <div class="fintech-card" style="border-left: 4px solid {PALETTE["warning"]};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-size: 1.15rem; font-weight: 700; color: {PALETTE["text"]};">
                                        {d_name}
                                    </span>
                                    <div style="font-size: 0.85rem; color: {PALETTE["text_secondary"]};">
                                        Scheduled Date: {d_due} • Amount: <strong style="color: {PALETTE["text"]};">{format_money(d_amt, d_curr)}</strong>
                                    </div>
                                </div>
                                <div>
                                    {render_badge("DUE FOR EXECUTION", "warning")}
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    col_exec_btn, _ = st.columns([1, 2])
                    with col_exec_btn:
                        if st.button(
                            f"Post to Ledger: {d_name}",
                            key=f"exec_due_{d_id}",
                            use_container_width=True,
                        ):
                            ex_ok, ex_res = api_client.execute_due_rule(d_id)
                            if ex_ok:
                                st.success(f"Successfully posted '{d_name}' to ledger!")
                                st.rerun()
                            else:
                                st.error(ex_res.get("message", "Failed to execute recurring rule."))

            st.markdown(
                "<hr style='border-color: #334155; margin: 1.5rem 0;'>", unsafe_allow_html=True
            )

        # 2. General Directory of Configured Recurring Rules
        r_ok, rules = api_client.list_recurring_rules(active_only=False)

        if not r_ok or not rules:
            if not (due_ok and due_rules):
                render_empty_state(
                    title="No Recurring Rules Configured",
                    message="Establish templates for periodic subscriptions, salaries, or utility bills to streamline ledger entries.",
                    icon="🔄",
                )
        else:
            st.markdown(f"#### Configured Schedules ({len(rules)})")
            for rule in rules:
                rule_id = rule.get("id", "")
                name = rule.get("name", "Untitled Rule")
                amt = Decimal(str(rule.get("amount", "0.00")))
                curr = rule.get("currency", "INR")
                tx_type = rule.get("transaction_type", "EXPENSE")
                freq = rule.get("frequency", "MONTHLY")
                interval = rule.get("interval", 1)
                next_occ = rule.get("next_occurrence", "")
                is_active = rule.get("is_active", True)
                notes = rule.get("notes")

                is_cancelled = bool(notes and "[CANCELLED]" in notes)
                if is_cancelled:
                    status_badge = render_badge("CANCELLED", "negative")
                elif is_active:
                    status_badge = render_badge("ACTIVE", "positive")
                else:
                    status_badge = render_badge("PAUSED", "secondary")

                type_badge = render_badge(
                    tx_type, "negative" if tx_type == "EXPENSE" else "positive"
                )

                with st.container():
                    st.markdown(
                        f"""
                        <div class="fintech-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                                <div>
                                    <span style="font-size: 1.2rem; font-weight: 700; color: {PALETTE["text"]};">
                                        {name}
                                    </span>
                                    <div style="font-size: 0.85rem; color: {PALETTE["text_secondary"]}; margin-top: 0.2rem;">
                                        Frequency: Every {interval} {freq.lower()} cycle(s) • Next: {next_occ}
                                    </div>
                                </div>
                                <div style="display: flex; gap: 0.5rem;">
                                    {type_badge}
                                    {status_badge}
                                </div>
                            </div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: {PALETTE["text"]}; margin-top: 0.5rem;">
                                {format_money(amt, curr)}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if notes:
                        st.caption(f"Notes: {notes}")

                    col_act1, col_act2, _ = st.columns([1, 1, 2])
                    with col_act1:
                        if not is_cancelled:
                            if is_active:
                                if st.button(
                                    "⏸ Pause",
                                    key=f"pause_{rule_id}",
                                    use_container_width=True,
                                ):
                                    p_ok, _ = api_client.pause_recurring_rule(rule_id)
                                    if p_ok:
                                        st.success(f"Paused '{name}'.")
                                        st.rerun()
                                    else:
                                        st.error("Failed to pause recurring rule.")
                            else:
                                if st.button(
                                    "▶ Resume",
                                    key=f"resume_{rule_id}",
                                    use_container_width=True,
                                ):
                                    res_ok, res_data = api_client.resume_recurring_rule(rule_id)
                                    if res_ok:
                                        st.success(f"Resumed '{name}'.")
                                        st.rerun()
                                    else:
                                        st.error(res_data.get("message", "Failed to resume recurring rule."))

                    with col_act2:
                        if not is_cancelled:
                            if st.button(
                                "❌ Cancel",
                                key=f"cancel_{rule_id}",
                                use_container_width=True,
                            ):
                                c_ok, c_data = api_client.cancel_recurring_rule(rule_id)
                                if c_ok:
                                    st.success(f"Cancelled schedule '{name}'.")
                                    st.rerun()
                                else:
                                    st.error(c_data.get("message", "Failed to cancel recurring rule."))

                    st.markdown(
                        "<hr style='border-color: #334155; margin: 1rem 0;'>",
                        unsafe_allow_html=True,
                    )

    # =========================================================================
    # TAB 2: CREATE RECURRING RULE
    # =========================================================================
    with tab_create:
        st.markdown("#### Establish a Recurring Schedule Template")
        st.caption(
            "Recurring templates define periodic ledger postings. Schedulers calculate next occurrence dates deterministically without automated background cron triggers."
        )

        acc_ok, accounts = api_client.list_accounts()

        if not acc_ok or not accounts:
            st.warning(
                "Please configure an account first before creating recurring transaction rules."
            )
        else:
            with st.form(key="create_recurring_rule_form"):
                acc_options = {f"{a['name']} ({a['currency']})": a["id"] for a in accounts}
                rule_acc_label = st.selectbox("Source Account *", options=list(acc_options.keys()))

                col_r1, col_r2 = st.columns([2, 1])
                with col_r1:
                    rule_name = st.text_input(
                        "Schedule Name *",
                        placeholder="e.g. Netflix Subscription, Monthly Salary, Rent",
                    )
                with col_r2:
                    tx_type_choice = st.selectbox(
                        "Transaction Type *",
                        options=["EXPENSE", "INCOME"],
                        index=0,
                    )

                col_r3, col_r4 = st.columns([1, 1])
                with col_r3:
                    rule_amount = st.number_input(
                        "Amount *",
                        min_value=1.00,
                        value=1500.00,
                        step=100.00,
                        format="%.2f",
                    )
                with col_r4:
                    currency = st.selectbox(
                        "Currency *",
                        options=["INR", "USD", "EUR", "GBP"],
                        index=0,
                    )

                col_r5, col_r6 = st.columns([1, 1])
                with col_r5:
                    frequency = st.selectbox(
                        "Recurrence Frequency *",
                        options=["DAILY", "WEEKLY", "BIWEEKLY", "MONTHLY", "QUARTERLY", "YEARLY"],
                        index=3,
                    )
                with col_r6:
                    interval = st.number_input(
                        "Interval Multiplier *",
                        min_value=1,
                        max_value=365,
                        value=1,
                        step=1,
                        help="e.g. 1 for every month, 2 for every 2 months",
                    )

                col_r7, col_r8 = st.columns([1, 1])
                with col_r7:
                    start_date = st.date_input("Start Date *", value=date.today())
                with col_r8:
                    has_end = st.checkbox("Set Expiration / End Date", value=False)
                    end_date = st.date_input("End Date", value=date.today()) if has_end else None

                rule_notes = st.text_area(
                    "Rule Description / Notes (optional)",
                    placeholder="Details about contract period, billing frequency, or vendor terms.",
                )

                submit_rule = st.form_submit_button(
                    "Create Recurring Rule",
                    use_container_width=True,
                )

                if submit_rule:
                    if not rule_name.strip():
                        st.error("Schedule name is required.")
                    elif rule_amount <= 0:
                        st.error("Schedule amount must be strictly positive.")
                    elif has_end and end_date and end_date < start_date:
                        st.error("End date cannot be earlier than start date.")
                    else:
                        payload = {
                            "account_id": acc_options[rule_acc_label],
                            "name": rule_name.strip(),
                            "amount": str(rule_amount),
                            "currency": currency,
                            "transaction_type": tx_type_choice,
                            "frequency": frequency,
                            "interval": int(interval),
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat() if has_end and end_date else None,
                            "category_id": None,
                            "notes": rule_notes.strip() if rule_notes else None,
                        }

                        c_ok, c_res = api_client.create_recurring_rule(payload)
                        if c_ok:
                            st.success(f"Recurring schedule '{rule_name}' created successfully!")
                            st.rerun()
                        else:
                            st.error(c_res.get("message", "Failed to create recurring rule."))
