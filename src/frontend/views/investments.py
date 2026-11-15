"""Investments view for portfolio holdings, security trades, and dividend receipts."""

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


def render_investments_view() -> None:
    """Render investment portfolio tracking, securities trading, and dividend logging."""
    render_header(
        title="Investment Portfolio & Holdings",
        subtitle="Track equity and fund assets, cost basis, trading transactions, and dividend distributions.",
        badge_text="Portfolio",
        badge_type="accent",
    )

    # Architectural disclaimer regarding market valuations
    st.markdown(
        f"""
        <div style="background-color: {PALETTE["surface_elevated"]}; border-left: 4px solid {PALETTE["accent"]}; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1.25rem;">
            <div style="font-size: 0.85rem; color: {PALETTE["text"]}; font-weight: 600;">Valuation Disclaimer</div>
            <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]};">
                Portfolio balances and positions reflect historical weighted-average cost basis. Real-time market valuation feeds and automated trading integrations are outside active architectural boundaries.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    acc_ok, accounts = api_client.list_accounts()
    account_map = {a["id"]: a for a in (accounts or [])}

    tab_holdings, tab_buy, tab_sell, tab_dividend = st.tabs(
        ["📈 Portfolio Holdings", "🛒 Buy Security", "💰 Sell Security", "💵 Record Dividend"]
    )

    # =========================================================================
    # TAB 1: PORTFOLIO HOLDINGS
    # =========================================================================
    with tab_holdings:
        # Optional filter by account
        selected_acc_id: str | None = None
        if accounts:
            filter_options = ["All Accounts"] + [f"{a['name']} ({a['currency']})" for a in accounts]
            filter_choice = st.selectbox("Filter Holdings by Account", options=filter_options)
            if filter_choice != "All Accounts":
                for a in accounts:
                    if f"{a['name']} ({a['currency']})" == filter_choice:
                        selected_acc_id = a["id"]
                        break

        h_ok, holdings = api_client.list_holdings(account_id=selected_acc_id)
        if not h_ok or not holdings:
            render_empty_state(
                title="No Active Holdings Found",
                message="Acquire securities using the 'Buy Security' tab to establish portfolio positions with weighted-average cost basis.",
                icon="📈",
            )
        else:
            for holding in holdings:
                asset_obj = holding.get("asset") or {}
                symbol = asset_obj.get("symbol") or f"Asset {holding.get('asset_id', '')[:8]}"
                name = asset_obj.get("name") or symbol
                asset_type = asset_obj.get("asset_type", "EQUITY")
                curr = holding.get("currency", "INR")
                qty = Decimal(str(holding.get("quantity", "0.0000")))
                cost_per_unit = Decimal(str(holding.get("cost_basis_per_unit", "0.00")))
                total_cost = Decimal(str(holding.get("total_cost", "0.00")))
                acc_id = holding.get("account_id", "")
                acc_name = account_map.get(acc_id, {}).get("name", "Account")

                with st.container():
                    st.markdown(
                        f"""
                        <div class="fintech-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                                <div>
                                    <span style="font-size: 1.25rem; font-weight: 700; color: {PALETTE["text"]};">
                                        {symbol}
                                    </span>
                                    <span style="font-size: 0.85rem; color: {PALETTE["text_secondary"]}; margin-left: 0.5rem;">
                                        {name} • Account: {acc_name}
                                    </span>
                                </div>
                                <div>
                                    {render_badge(asset_type, "accent")}
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 0.5rem;">
                                <div>
                                    <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]};">Units Held</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: {PALETTE["text"]};">{qty:.4f}</div>
                                </div>
                                <div>
                                    <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]};">Cost Basis / Unit</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: {PALETTE["text"]};">{format_money(cost_per_unit, curr)}</div>
                                </div>
                                <div>
                                    <div style="font-size: 0.8rem; color: {PALETTE["text_secondary"]};">Total Cost Basis</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: {PALETTE["positive"]};">{format_money(total_cost, curr)}</div>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # =========================================================================
    # TAB 2: BUY SECURITY
    # =========================================================================
    with tab_buy:
        st.markdown("#### Execute Security Purchase")
        st.caption(
            "Acquiring shares updates total units and recomputes the weighted-average cost basis per unit."
        )

        if not accounts:
            st.warning("Please configure an account first before trading securities.")
        else:
            with st.form(key="buy_security_form"):
                acc_options = {f"{a['name']} ({a['currency']})": a["id"] for a in accounts}
                b_acc_label = st.selectbox("Trading Account *", options=list(acc_options.keys()))

                b_asset_id = st.text_input(
                    "Asset ID / UUID *",
                    placeholder="Enter valid Asset UUID (e.g. from existing holdings or system catalog)",
                )

                col_b1, col_b2 = st.columns([1, 1])
                with col_b1:
                    b_qty = st.number_input(
                        "Quantity *",
                        min_value=0.0001,
                        value=10.0000,
                        step=1.0000,
                        format="%.4f",
                    )
                with col_b2:
                    b_price = st.number_input(
                        "Purchase Price per Unit *",
                        min_value=0.01,
                        value=100.00,
                        step=10.00,
                        format="%.2f",
                    )

                col_b3, col_b4 = st.columns([1, 1])
                with col_b3:
                    b_fees = st.number_input(
                        "Brokerage / Exchange Fees",
                        min_value=0.00,
                        value=0.00,
                        step=1.00,
                        format="%.2f",
                    )
                with col_b4:
                    b_date = st.date_input("Transaction Date", value=date.today())

                b_notes = st.text_area(
                    "Trade Notes (optional)",
                    placeholder="e.g. SIP installment, lump sum equity allocation",
                )

                submit_buy = st.form_submit_button(
                    "Execute Purchase Order", use_container_width=True
                )

                if submit_buy:
                    if not b_asset_id.strip():
                        st.error("Asset ID is required.")
                    elif b_qty <= 0 or b_price <= 0:
                        st.error("Quantity and price must be strictly positive.")
                    else:
                        payload = {
                            "account_id": acc_options[b_acc_label],
                            "asset_id": b_asset_id.strip(),
                            "quantity": str(b_qty),
                            "price_per_unit": str(b_price),
                            "fees": str(b_fees),
                            "transaction_date": b_date.isoformat(),
                            "notes": b_notes.strip() if b_notes else None,
                        }
                        ok, res = api_client.buy_security(payload)
                        if ok:
                            st.success(
                                f"Successfully purchased {b_qty:.4f} units! Updated position recorded."
                            )
                            st.rerun()
                        else:
                            st.error(res.get("message", "Failed to execute security purchase."))

    # =========================================================================
    # TAB 3: SELL SECURITY
    # =========================================================================
    with tab_sell:
        st.markdown("#### Liquidate Security Position")
        st.caption(
            "Selling securities verifies quantity sufficiency, computes realized capital gains/losses, and updates remaining holdings."
        )

        if not accounts:
            st.warning("Please configure an account first.")
        else:
            with st.form(key="sell_security_form"):
                acc_options = {f"{a['name']} ({a['currency']})": a["id"] for a in accounts}
                s_acc_label = st.selectbox("Trading Account *", options=list(acc_options.keys()))

                s_asset_id = st.text_input(
                    "Asset ID / UUID *",
                    placeholder="Enter valid Asset UUID to sell",
                )

                col_s1, col_s2 = st.columns([1, 1])
                with col_s1:
                    s_qty = st.number_input(
                        "Quantity to Sell *",
                        min_value=0.0001,
                        value=5.0000,
                        step=1.0000,
                        format="%.4f",
                    )
                with col_s2:
                    s_price = st.number_input(
                        "Selling Price per Unit *",
                        min_value=0.01,
                        value=120.00,
                        step=10.00,
                        format="%.2f",
                    )

                col_s3, col_s4 = st.columns([1, 1])
                with col_s3:
                    s_fees = st.number_input(
                        "Selling Fees / STT",
                        min_value=0.00,
                        value=0.00,
                        step=1.00,
                        format="%.2f",
                    )
                with col_s4:
                    s_date = st.date_input("Sale Date", value=date.today())

                s_notes = st.text_area("Sale Notes (optional)")

                submit_sell = st.form_submit_button(
                    "Execute Sale & Compute Realized P&L", use_container_width=True
                )

                if submit_sell:
                    if not s_asset_id.strip():
                        st.error("Asset ID is required.")
                    elif s_qty <= 0 or s_price <= 0:
                        st.error("Quantity and selling price must be strictly positive.")
                    else:
                        payload = {
                            "account_id": acc_options[s_acc_label],
                            "asset_id": s_asset_id.strip(),
                            "quantity": str(s_qty),
                            "price_per_unit": str(s_price),
                            "fees": str(s_fees),
                            "transaction_date": s_date.isoformat(),
                            "notes": s_notes.strip() if s_notes else None,
                        }
                        ok, res = api_client.sell_security(payload)
                        if ok and isinstance(res, dict):
                            realized_pnl = Decimal(str(res.get("realized_gain_loss", "0.00")))
                            is_gain = res.get("is_gain", realized_pnl >= 0)
                            pnl_color = PALETTE["positive"] if is_gain else PALETTE["negative"]

                            st.success("Sale order executed successfully!")
                            st.markdown(
                                f"""
                                <div class="fintech-card" style="border: 1px solid {pnl_color};">
                                    <h4 style="color: {pnl_color}; margin-top: 0;">
                                        Realized Capital {"Gain" if is_gain else "Loss"}: {format_money(realized_pnl)}
                                    </h4>
                                    <div style="font-size: 0.9rem; color: {PALETTE["text_secondary"]};">
                                        Gross Proceeds: <strong>{format_money(res.get("gross_proceeds", "0.00"))}</strong> •
                                        Net Proceeds: <strong>{format_money(res.get("net_proceeds", "0.00"))}</strong> •
                                        Cost Basis Relieved: <strong>{format_money(res.get("total_cost_basis", "0.00"))}</strong>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.error(res.get("message", "Failed to execute security sale."))

    # =========================================================================
    # TAB 4: RECORD DIVIDEND
    # =========================================================================
    with tab_dividend:
        st.markdown("#### Record Dividend Earnings")
        st.caption(
            "Dividends record investment income directly to your account without altering held share quantities."
        )

        if not accounts:
            st.warning("Please configure an account first.")
        else:
            with st.form(key="record_dividend_form"):
                acc_options = {f"{a['name']} ({a['currency']})": a["id"] for a in accounts}
                d_acc_label = st.selectbox(
                    "Deposit Account *", options=list(acc_options.keys()), key="div_acc_sel"
                )

                d_asset_id = st.text_input(
                    "Asset ID / UUID *",
                    placeholder="Enter valid Asset UUID paying the dividend",
                    key="div_asset_id_input",
                )

                col_d1, col_d2 = st.columns([1, 1])
                with col_d1:
                    d_amount = st.number_input(
                        "Dividend Amount Received *",
                        min_value=0.01,
                        value=500.00,
                        step=50.00,
                        format="%.2f",
                        key="div_amount_input",
                    )
                with col_d2:
                    d_date = st.date_input("Receipt Date", value=date.today(), key="div_date_input")

                d_notes = st.text_area("Dividend Notes (optional)", key="div_notes_input")

                submit_div = st.form_submit_button(
                    "Record Dividend Receipt", use_container_width=True
                )

                if submit_div:
                    if not d_asset_id.strip():
                        st.error("Asset ID is required.")
                    elif d_amount <= 0:
                        st.error("Dividend amount must be strictly positive.")
                    else:
                        payload = {
                            "account_id": acc_options[d_acc_label],
                            "asset_id": d_asset_id.strip(),
                            "amount": str(d_amount),
                            "transaction_date": d_date.isoformat(),
                            "notes": d_notes.strip() if d_notes else None,
                        }
                        ok, res = api_client.record_dividend(payload)
                        if ok:
                            st.success(
                                f"Dividend of {format_money(d_amount)} recorded successfully!"
                            )
                            st.rerun()
                        else:
                            st.error(res.get("message", "Failed to record dividend."))
