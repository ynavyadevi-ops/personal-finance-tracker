"""Loans and debt liabilities view for amortization schedules and repayment tracking."""

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


def render_loans_view() -> None:
    """Render loan liability management, amortization schedules, and debt tracking."""
    render_header(
        title="Loans & Debt Liabilities",
        subtitle="Monitor borrowing liabilities, track amortization schedules, and log installment repayments.",
        badge_text="Debt Tracking",
        badge_type="warning",
    )

    tab_overview, tab_create = st.tabs(["📉 Active Liabilities", "➕ Record Loan Obligation"])

    # =========================================================================
    # TAB 1: ACTIVE LOANS & AMORTIZATION SCHEDULES
    # =========================================================================
    with tab_overview:
        ok, loans = api_client.list_loans()
        if not ok or not loans:
            render_empty_state(
                title="No Loan Liabilities Found",
                message="Record personal, mortgage, or auto loans to track monthly amortization schedules and principal reduction.",
                icon="📉",
            )
        else:
            for loan in loans:
                loan_id = loan.get("id", "")
                lender = loan.get("lender_name", "Unknown Lender")
                principal = Decimal(str(loan.get("principal_amount", "0.00")))
                balance = Decimal(str(loan.get("remaining_balance", "0.00")))
                rate = Decimal(str(loan.get("interest_rate", "0.00")))
                term = loan.get("term_months", 0)
                monthly_emi = Decimal(str(loan.get("minimum_monthly_payment", "0.00")))
                is_settled = loan.get("is_settled", False)
                start_date_str = loan.get("start_date")
                notes = loan.get("notes")

                badge_type = "positive" if is_settled else "warning"
                status_text = "SETTLED" if is_settled else "ACTIVE"

                with st.container():
                    st.markdown(
                        f"""
                        <div class="fintech-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                                <div>
                                    <span style="font-size: 1.25rem; font-weight: 700; color: {PALETTE["text"]};">
                                        {lender}
                                    </span>
                                    <div style="font-size: 0.85rem; color: {PALETTE["text_secondary"]}; margin-top: 0.2rem;">
                                        Started: {start_date_str} • Term: {term} Months • Rate: {rate}% p.a.
                                    </div>
                                </div>
                                <div>
                                    {render_badge(status_text, badge_type)}
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 0.5rem;">
                                <div>
                                    <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]};">Principal</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: {PALETTE["text"]};">{format_money(principal)}</div>
                                </div>
                                <div>
                                    <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]};">Remaining Balance</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: {PALETTE["negative"] if balance > 0 else PALETTE["positive"]};">
                                        {format_money(balance)}
                                    </div>
                                </div>
                                <div>
                                    <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]};">Monthly EMI</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: {PALETTE["text"]};">{format_money(monthly_emi)}</div>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if notes:
                        st.caption(f"Notes: {notes}")

                    # Amortization Schedule & Repayment Expander
                    with st.expander(
                        f"Amortization Schedule & Repayment — {lender}", expanded=False
                    ):
                        d_ok, loan_details = api_client.get_loan(loan_id)
                        if not d_ok or not isinstance(loan_details, dict):
                            st.warning(
                                "Unable to fetch complete amortization schedule for this loan."
                            )
                        else:
                            schedules = loan_details.get("payment_schedules", [])
                            if not schedules:
                                st.info("No amortization schedule generated for this liability.")
                            else:
                                unpaid_schedules = [s for s in schedules if not s.get("is_paid")]
                                paid_count = len(schedules) - len(unpaid_schedules)

                                st.markdown(
                                    f"**Repayment Progress**: {paid_count} / {len(schedules)} installments completed"
                                )

                                # Form to record installment payment
                                if unpaid_schedules and not is_settled:
                                    st.markdown("##### 💳 Record Installment Payment")
                                    with st.form(key=f"pay_installment_{loan_id}"):
                                        unpaid_numbers = [
                                            s.get("payment_number") for s in unpaid_schedules
                                        ]
                                        selected_payment_num = st.selectbox(
                                            "Select Installment Number to Pay",
                                            options=unpaid_numbers,
                                            format_func=lambda n: f"Installment #{n} (Due: next schedule)",
                                        )
                                        st.caption(
                                            "Recording an installment updates the remaining principal balance and marks the payment schedule as fulfilled."
                                        )

                                        if st.form_submit_button(
                                            "Confirm Installment Payment", use_container_width=True
                                        ):
                                            if selected_payment_num:
                                                p_ok, p_res = api_client.record_loan_payment(
                                                    loan_id=loan_id,
                                                    payment_number=int(selected_payment_num),
                                                )
                                                if p_ok:
                                                    st.success(
                                                        f"Successfully recorded payment for installment #{selected_payment_num}!"
                                                    )
                                                    st.rerun()
                                                else:
                                                    st.error(
                                                        p_res.get(
                                                            "message",
                                                            "Failed to record loan payment.",
                                                        )
                                                    )

                                # Amortization table summary
                                st.markdown("##### 📋 Installment Breakdown")
                                schedule_rows = []
                                for s in schedules[
                                    :24
                                ]:  # Show first 24 installments for readability
                                    schedule_rows.append(
                                        {
                                            "Inst #": s.get("payment_number"),
                                            "Due Date": s.get("due_date"),
                                            "Principal": format_money(
                                                s.get("principal_component", "0.00")
                                            ),
                                            "Interest": format_money(
                                                s.get("interest_component", "0.00")
                                            ),
                                            "Total Payment": format_money(
                                                s.get("total_payment", "0.00")
                                            ),
                                            "Balance": format_money(
                                                s.get("remaining_balance", "0.00")
                                            ),
                                            "Status": "PAID" if s.get("is_paid") else "DUE",
                                        }
                                    )
                                st.dataframe(
                                    schedule_rows, use_container_width=True, hide_index=True
                                )
                                if len(schedules) > 24:
                                    st.caption(
                                        f"Showing first 24 of {len(schedules)} installments."
                                    )

                    st.markdown(
                        "<hr style='border-color: #334155; margin: 1rem 0;'>",
                        unsafe_allow_html=True,
                    )

    # =========================================================================
    # TAB 2: RECORD LOAN OBLIGATION
    # =========================================================================
    with tab_create:
        st.markdown("#### Record a New Loan Liability")
        st.caption(
            "Recording a loan binds a liability obligation to an account, generating standard fixed-rate amortization schedules."
        )

        acc_ok, accounts = api_client.list_accounts()
        if not acc_ok or not accounts:
            st.warning("Please create an account first before establishing a loan obligation.")
        else:
            with st.form(key="create_loan_form"):
                acc_options = {
                    f"{a['name']} ({a['currency']}) - {a.get('account_type', 'ACCOUNT')}": a["id"]
                    for a in accounts
                }
                selected_acc_label = st.selectbox(
                    "Associated Account *",
                    options=list(acc_options.keys()),
                )

                col_l1, col_l2 = st.columns([2, 1])
                with col_l1:
                    lender_name = st.text_input(
                        "Lender / Creditor Name *",
                        placeholder="e.g. HDFC Bank, Chase, Personal Loan",
                    )
                with col_l2:
                    principal_amount = st.number_input(
                        "Principal Borrowed Amount *",
                        min_value=100.00,
                        value=500000.00,
                        step=10000.00,
                        format="%.2f",
                    )

                col_l3, col_l4 = st.columns([1, 1])
                with col_l3:
                    interest_rate = st.number_input(
                        "Annual Interest Rate (%) *",
                        min_value=0.00,
                        max_value=100.00,
                        value=8.50,
                        step=0.25,
                        format="%.2f",
                    )
                with col_l4:
                    term_months = st.number_input(
                        "Term Duration (Months) *",
                        min_value=1,
                        max_value=600,
                        value=36,
                        step=12,
                    )

                col_l5, col_l6 = st.columns([1, 1])
                with col_l5:
                    start_date = st.date_input("Loan Start Date", value=date.today())
                with col_l6:
                    has_due = st.checkbox("Set Final Maturity Due Date", value=False)
                    due_date = (
                        st.date_input("Maturity Due Date", value=date.today()) if has_due else None
                    )

                loan_notes = st.text_area(
                    "Notes & Terms (optional)",
                    placeholder="e.g. Fixed rate home loan, collateralized against property.",
                )

                submit_loan = st.form_submit_button(
                    "Record Loan Liability",
                    use_container_width=True,
                )

                if submit_loan:
                    account_id = acc_options[selected_acc_label]
                    if not lender_name.strip():
                        st.error("Lender name is required.")
                    elif principal_amount <= 0:
                        st.error("Principal borrowed amount must be strictly positive.")
                    else:
                        payload = {
                            "account_id": account_id,
                            "lender_name": lender_name.strip(),
                            "principal_amount": str(principal_amount),
                            "interest_rate": str(interest_rate),
                            "interest_type": "FIXED",
                            "term_months": int(term_months),
                            "start_date": start_date.isoformat(),
                            "due_date": due_date.isoformat() if due_date else None,
                            "notes": loan_notes.strip() if loan_notes else None,
                        }

                        c_ok, c_res = api_client.create_loan(payload)
                        if c_ok:
                            st.success(
                                f"Loan obligation for '{lender_name}' recorded with {term_months} monthly installments!"
                            )
                            st.rerun()
                        else:
                            st.error(c_res.get("message", "Failed to create loan liability."))
