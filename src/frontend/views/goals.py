"""Savings goals view for milestone tracking, contributions, and withdrawals."""

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


def render_goals_view() -> None:
    """Render savings goals and milestone tracking interface."""
    render_header(
        title="Savings Goals & Milestones",
        subtitle="Establish financial target milestones, track funded progress, and manage contributions.",
        badge_text="Milestones",
        badge_type="accent",
    )

    tab_overview, tab_create = st.tabs(["🎯 Active Milestones", "➕ Create Savings Goal"])

    # =========================================================================
    # TAB 1: ACTIVE GOALS & PROGRESS
    # =========================================================================
    with tab_overview:
        ok, goals = api_client.list_goals()
        if not ok or not goals:
            render_empty_state(
                title="No Savings Goals Established",
                message="Define target financial milestones to systematically allocate savings and monitor your progress.",
                icon="🎯",
            )
        else:
            for goal in goals:
                goal_id = goal.get("id", "")
                name = goal.get("name", "Untitled Goal")
                curr = goal.get("currency", "INR")
                target = Decimal(str(goal.get("target_amount", "0.00")))
                current = Decimal(str(goal.get("current_amount", "0.00")))
                is_achieved = goal.get("is_achieved", False)
                target_date_str = goal.get("target_date")
                notes = goal.get("notes")

                remaining = max(Decimal("0.00"), target - current)
                progress_pct = (
                    float(min(Decimal("1.0"), current / target))
                    if target > Decimal("0.00")
                    else 0.0
                )
                progress_display = round(progress_pct * 100, 1)

                badge_type = "positive" if is_achieved else "accent"
                status_text = "ACHIEVED" if is_achieved else "IN PROGRESS"

                with st.container():
                    st.markdown(
                        f"""
                        <div class="fintech-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                                <div>
                                    <span style="font-size: 1.2rem; font-weight: 700; color: {PALETTE["text"]};">
                                        {name}
                                    </span>
                                    {f'<div style="font-size: 0.85rem; color: {PALETTE["text_secondary"]}; margin-top: 0.2rem;">Target Date: {target_date_str}</div>' if target_date_str else ""}
                                </div>
                                <div>
                                    {render_badge(status_text, badge_type)}
                                </div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; color: {PALETTE["text_secondary"]}; margin-bottom: 0.4rem;">
                                <span>Funded: <strong style="color: {PALETTE["text"]};">{format_money(current, curr)}</strong></span>
                                <span>Target: <strong style="color: {PALETTE["text"]};">{format_money(target, curr)}</strong></span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.progress(progress_pct)
                    st.caption(
                        f"Progress: {progress_display}% • Remaining: {format_money(remaining, curr)}"
                        + (f" • Notes: {notes}" if notes else "")
                    )

                    # Expandable Goal Actions (Contribute & Withdraw)
                    with st.expander(f"Manage Funds — {name}", expanded=False):
                        col_contrib, col_withdraw = st.columns([1, 1])

                        with col_contrib:
                            st.markdown("##### 📥 Add Contribution")
                            with st.form(key=f"contrib_form_{goal_id}"):
                                contrib_amount = st.number_input(
                                    f"Amount ({curr})",
                                    min_value=0.01,
                                    step=100.0,
                                    format="%.2f",
                                    key=f"contrib_amt_{goal_id}",
                                )
                                contrib_notes = st.text_input(
                                    "Contribution Notes (optional)",
                                    key=f"contrib_notes_{goal_id}",
                                )
                                if st.form_submit_button(
                                    "Record Contribution", use_container_width=True
                                ):
                                    c_ok, c_res = api_client.contribute_to_goal(
                                        goal_id=goal_id,
                                        amount=str(contrib_amount),
                                        notes=contrib_notes or None,
                                    )
                                    if c_ok:
                                        st.success(
                                            f"Successfully contributed {format_money(contrib_amount, curr)} to {name}!"
                                        )
                                        st.rerun()
                                    else:
                                        st.error(
                                            c_res.get(
                                                "message", "Failed to record goal contribution."
                                            )
                                        )

                        with col_withdraw:
                            st.markdown("##### 📤 Withdraw Funds")
                            with st.form(key=f"withdraw_form_{goal_id}"):
                                withdraw_amount = st.number_input(
                                    f"Amount ({curr})",
                                    min_value=0.01,
                                    max_value=float(current) if current > 0 else 0.01,
                                    step=100.0,
                                    format="%.2f",
                                    key=f"withdraw_amt_{goal_id}",
                                )
                                if st.form_submit_button(
                                    "Record Withdrawal", use_container_width=True
                                ):
                                    w_ok, w_res = api_client.withdraw_from_goal(
                                        goal_id=goal_id,
                                        amount=str(withdraw_amount),
                                    )
                                    if w_ok:
                                        st.success(
                                            f"Successfully withdrew {format_money(withdraw_amount, curr)} from {name}."
                                        )
                                        st.rerun()
                                    else:
                                        st.error(
                                            w_res.get("message", "Failed to process withdrawal.")
                                        )

                    st.markdown(
                        "<hr style='border-color: #334155; margin: 1rem 0;'>",
                        unsafe_allow_html=True,
                    )

    # =========================================================================
    # TAB 2: CREATE GOAL
    # =========================================================================
    with tab_create:
        st.markdown("#### Establish a New Savings Milestone")
        st.caption(
            "Savings milestones track dedicated allocations towards personal financial objectives without affecting income/expense balances."
        )

        with st.form(key="create_savings_goal_form"):
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                goal_name = st.text_input(
                    "Goal Name *",
                    placeholder="e.g. Emergency Fund, House Downpayment, Vacation",
                )
            with col_g2:
                currency = st.selectbox(
                    "Target Currency *",
                    options=["INR", "USD", "EUR", "GBP"],
                    index=0,
                )

            col_g3, col_g4 = st.columns([1, 1])
            with col_g3:
                target_amount = st.number_input(
                    f"Target Milestone Amount ({currency}) *",
                    min_value=1.00,
                    value=50000.00,
                    step=5000.00,
                    format="%.2f",
                )
            with col_g4:
                has_target_date = st.checkbox("Set Target Completion Date", value=True)
                target_date = (
                    st.date_input(
                        "Target Date",
                        value=date.today(),
                    )
                    if has_target_date
                    else None
                )

            notes = st.text_area(
                "Goal Description / Notes (optional)",
                placeholder="Details regarding purpose, target institution, or milestones.",
            )

            submit_create = st.form_submit_button(
                "Create Savings Goal",
                use_container_width=True,
            )

            if submit_create:
                if not goal_name.strip():
                    st.error("Goal name is required.")
                elif target_amount <= 0:
                    st.error("Target milestone amount must be strictly positive.")
                else:
                    payload = {
                        "name": goal_name.strip(),
                        "target_amount": str(target_amount),
                        "currency": currency,
                        "target_date": target_date.isoformat() if target_date else None,
                        "notes": notes.strip() if notes else None,
                    }

                    ok, res = api_client.create_goal(payload)
                    if ok:
                        st.success(f"Savings goal '{goal_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("message", "Failed to create savings goal."))
