"""Financial Analytics Engine providing deterministic cash flow metrics, rollups, and rule-based insights."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.core.money import to_decimal


class FinancialAnalyticsEngine:
    """Deterministic financial analytics and calculation engine.

    Enforces:
    - Decimal precision on all monetary values (zero float rounding drift).
    - Strict exclusion of inter-account transfers from income and expenses.
    - Reversal compensation handling.
    - Currency isolation (no silent cross-currency mixing).
    - Rule-based deterministic financial insights with transparent calculation steps.
    """

    @staticmethod
    def _parse_date(dt_val: str | date | datetime | None) -> date | None:
        """Parse varied date formats to standard datetime.date."""
        if dt_val is None:
            return None
        if isinstance(dt_val, datetime):
            return dt_val.date()
        if isinstance(dt_val, date):
            return dt_val
        try:
            return date.fromisoformat(str(dt_val).split("T")[0])
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _is_reversed_or_reversal(tx: dict[str, Any]) -> bool:
        """Check if transaction is a reversal or marked as reversed."""
        desc = (tx.get("description") or "").lower()
        notes = (tx.get("notes") or "").lower()
        tags = [str(t).lower() for t in (tx.get("tags") or [])]
        return (
            "reversal of" in desc or "reversal" in tags or "reversed" in tags or "reversal" in notes
        )

    def calculate_cash_flow(
        self,
        transactions: list[dict[str, Any]],
        currency: str = "INR",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Aggregate total income, total expenses, and net cash flow for a specific currency."""
        target_currency = (currency or "INR").strip().upper()
        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")
        tx_count = 0

        for tx in transactions:
            tx_curr = (tx.get("currency") or "INR").strip().upper()
            if tx_curr != target_currency:
                continue

            # Date range filtering
            tx_date = self._parse_date(tx.get("transaction_date"))
            if tx_date:
                if start_date and tx_date < start_date:
                    continue
                if end_date and tx_date > end_date:
                    continue

            tx_type = str(tx.get("transaction_type") or "").upper()
            amt = to_decimal(tx.get("amount", "0.00"))

            # Exclude transfers and reversals
            if tx_type == "TRANSFER" or self._is_reversed_or_reversal(tx):
                continue

            if tx_type == "INCOME":
                total_income += amt
                tx_count += 1
            elif tx_type == "EXPENSE":
                total_expense += amt
                tx_count += 1

        net_cash_flow = total_income - total_expense
        savings_rate = (
            (net_cash_flow / total_income * Decimal("100.00")).quantize(Decimal("0.01"))
            if total_income > Decimal("0.00")
            else Decimal("0.00")
        )

        return {
            "currency": target_currency,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_cash_flow": net_cash_flow,
            "savings_rate_pct": savings_rate,
            "transaction_count": tx_count,
        }

    def calculate_spending_by_category(
        self,
        transactions: list[dict[str, Any]],
        currency: str = "INR",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Compute category-wise expense breakdown and proportion of total expenses."""
        target_currency = (currency or "INR").strip().upper()
        category_totals: dict[str, Decimal] = {}
        total_expense = Decimal("0.00")

        for tx in transactions:
            tx_curr = (tx.get("currency") or "INR").strip().upper()
            if tx_curr != target_currency:
                continue

            tx_date = self._parse_date(tx.get("transaction_date"))
            if tx_date:
                if start_date and tx_date < start_date:
                    continue
                if end_date and tx_date > end_date:
                    continue

            tx_type = str(tx.get("transaction_type") or "").upper()
            if tx_type != "EXPENSE" or self._is_reversed_or_reversal(tx):
                continue

            amt = to_decimal(tx.get("amount", "0.00"))
            cat_name = tx.get("category_name") or tx.get("category") or "Uncategorized"
            category_totals[cat_name] = category_totals.get(cat_name, Decimal("0.00")) + amt
            total_expense += amt

        results: list[dict[str, Any]] = []
        for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            pct = (
                (amt / total_expense * Decimal("100.00")).quantize(Decimal("0.1"))
                if total_expense > Decimal("0.00")
                else Decimal("0.0")
            )
            results.append(
                {
                    "category": cat,
                    "amount": amt,
                    "percentage": float(pct),
                    "currency": target_currency,
                }
            )

        return results

    def calculate_monthly_trends(
        self,
        transactions: list[dict[str, Any]],
        currency: str = "INR",
        months_count: int = 6,
    ) -> list[dict[str, Any]]:
        """Calculate month-over-month income, expense, and net cash flow trends."""
        target_currency = (currency or "INR").strip().upper()
        monthly_map: dict[str, dict[str, Decimal]] = {}

        for tx in transactions:
            tx_curr = (tx.get("currency") or "INR").strip().upper()
            if tx_curr != target_currency:
                continue

            tx_date = self._parse_date(tx.get("transaction_date"))
            if not tx_date:
                continue

            month_key = tx_date.strftime("%Y-%m")
            if month_key not in monthly_map:
                monthly_map[month_key] = {"income": Decimal("0.00"), "expense": Decimal("0.00")}

            tx_type = str(tx.get("transaction_type") or "").upper()
            if tx_type == "TRANSFER" or self._is_reversed_or_reversal(tx):
                continue

            amt = to_decimal(tx.get("amount", "0.00"))
            if tx_type == "INCOME":
                monthly_map[month_key]["income"] += amt
            elif tx_type == "EXPENSE":
                monthly_map[month_key]["expense"] += amt

        sorted_months = sorted(monthly_map.keys())[-months_count:]
        trends: list[dict[str, Any]] = []

        for m in sorted_months:
            data = monthly_map[m]
            inc = data["income"]
            exp = data["expense"]
            trends.append(
                {
                    "month": m,
                    "income": inc,
                    "expense": exp,
                    "net_flow": inc - exp,
                    "currency": target_currency,
                }
            )

        return trends

    def calculate_account_balance_distribution(
        self,
        accounts: list[dict[str, Any]],
        currency: str = "INR",
    ) -> list[dict[str, Any]]:
        """Compute balance distribution across accounts for a single currency."""
        target_currency = (currency or "INR").strip().upper()
        filtered = [
            a for a in accounts if (a.get("currency") or "INR").strip().upper() == target_currency
        ]

        total_balance = sum(
            [
                to_decimal(a.get("current_balance", a.get("opening_balance", "0.00")))
                for a in filtered
            ],
            Decimal("0.00"),
        )

        results: list[dict[str, Any]] = []
        for a in filtered:
            bal = to_decimal(a.get("current_balance", a.get("opening_balance", "0.00")))
            pct = (
                (bal / total_balance * Decimal("100.00")).quantize(Decimal("0.1"))
                if total_balance > Decimal("0.00")
                else Decimal("0.0")
            )
            results.append(
                {
                    "account_id": a.get("id"),
                    "name": a.get("name", "Account"),
                    "account_type": a.get("account_type", "CHECKING"),
                    "balance": bal,
                    "percentage": float(pct),
                    "currency": target_currency,
                }
            )

        return sorted(results, key=lambda x: x["balance"], reverse=True)

    def calculate_budget_vs_actual(
        self,
        budgets: list[dict[str, Any]],
        utilizations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Reconcile allocated category budgets against actual monthly expenditure."""
        util_map = {u.get("category_id"): u for u in utilizations if u.get("category_id")}
        results: list[dict[str, Any]] = []

        for b in budgets:
            cat_id = b.get("category_id")
            util = util_map.get(cat_id, {})
            cat_name = util.get("category_name", f"Category {str(cat_id)[:8]}")
            budgeted = to_decimal(b.get("amount", "0.00"))
            spent = to_decimal(util.get("spent_amount", "0.00"))
            remaining = budgeted - spent
            pct = (
                (spent / budgeted * Decimal("100.00")).quantize(Decimal("0.1"))
                if budgeted > Decimal("0.00")
                else Decimal("0.0")
            )
            status = util.get("status", "NORMAL")
            if spent > budgeted:
                status = "EXCEEDED"
            elif pct >= Decimal("80.0"):
                status = "WARNING"

            results.append(
                {
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "budgeted_amount": budgeted,
                    "spent_amount": spent,
                    "remaining_amount": remaining,
                    "utilization_percentage": float(pct),
                    "status": status,
                    "is_overspent": spent > budgeted,
                }
            )

        return sorted(results, key=lambda x: x["spent_amount"], reverse=True)

    def calculate_savings_progress(
        self,
        goals: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Calculate savings milestone progress metrics."""
        results: list[dict[str, Any]] = []
        for g in goals:
            target = to_decimal(g.get("target_amount", "0.00"))
            current = to_decimal(g.get("current_amount", "0.00"))
            curr = g.get("currency", "INR")
            remaining = max(Decimal("0.00"), target - current)
            pct = (
                (current / target * Decimal("100.00")).quantize(Decimal("0.1"))
                if target > Decimal("0.00")
                else Decimal("0.0")
            )
            results.append(
                {
                    "id": g.get("id"),
                    "name": g.get("name", "Savings Goal"),
                    "target_amount": target,
                    "current_amount": current,
                    "remaining_amount": remaining,
                    "progress_percentage": float(pct),
                    "is_achieved": g.get("is_achieved", current >= target),
                    "currency": curr,
                }
            )
        return results

    def calculate_investment_cost_basis_summary(
        self,
        holdings: list[dict[str, Any]],
        currency: str = "INR",
    ) -> dict[str, Any]:
        """Aggregate total portfolio acquisition cost basis without live price fabrication."""
        target_currency = (currency or "INR").strip().upper()
        filtered = [
            h for h in holdings if (h.get("currency") or "INR").strip().upper() == target_currency
        ]

        total_cost = sum(
            [to_decimal(h.get("total_cost", "0.00")) for h in filtered], Decimal("0.00")
        )
        position_rows: list[dict[str, Any]] = []

        for h in filtered:
            asset_info = h.get("asset") or {}
            symbol = asset_info.get("symbol") or f"Asset {str(h.get('asset_id'))[:8]}"
            name = asset_info.get("name") or symbol
            cost = to_decimal(h.get("total_cost", "0.00"))
            qty = to_decimal(h.get("quantity", "0.0000"))
            pct = (
                (cost / total_cost * Decimal("100.00")).quantize(Decimal("0.1"))
                if total_cost > Decimal("0.00")
                else Decimal("0.0")
            )
            position_rows.append(
                {
                    "symbol": symbol,
                    "name": name,
                    "quantity": qty,
                    "total_cost": cost,
                    "cost_basis_per_unit": to_decimal(h.get("cost_basis_per_unit", "0.00")),
                    "allocation_pct": float(pct),
                    "currency": target_currency,
                }
            )

        return {
            "currency": target_currency,
            "total_invested_cost": total_cost,
            "positions_count": len(position_rows),
            "positions": sorted(position_rows, key=lambda x: x["total_cost"], reverse=True),
            "valuation_disclaimer": "Cost basis reflects historical acquisition costs; live market valuations are not modeled.",
        }

    def generate_rule_based_insights(
        self,
        transactions: list[dict[str, Any]],
        budgets: list[dict[str, Any]] | None = None,
        utilizations: list[dict[str, Any]] | None = None,
        goals: list[dict[str, Any]] | None = None,
        loans: list[dict[str, Any]] | None = None,
        recurring_rules: list[dict[str, Any]] | None = None,
        currency: str = "INR",
    ) -> list[dict[str, Any]]:
        """Generate deterministic, explainable financial observations and rules-based insights."""
        insights: list[dict[str, Any]] = []
        target_currency = (currency or "INR").strip().upper()

        # 1. Cash Flow Health
        cf = self.calculate_cash_flow(transactions, currency=target_currency)
        inc = cf["total_income"]
        exp = cf["total_expense"]
        net = cf["net_cash_flow"]

        if inc > Decimal("0.00") or exp > Decimal("0.00"):
            if net > Decimal("0.00"):
                insights.append(
                    {
                        "category": "CASH_FLOW",
                        "severity": "positive",
                        "title": "Positive Net Cash Flow",
                        "description": f"You have generated a net cash surplus of {target_currency} {net:,.2f} with a savings rate of {cf['savings_rate_pct']}%.",
                        "calculation": f"Income ({inc:,.2f}) - Expenses ({exp:,.2f}) = Surplus ({net:,.2f}).",
                        "is_fact": True,
                    }
                )
            elif net < Decimal("0.00"):
                insights.append(
                    {
                        "category": "CASH_FLOW",
                        "severity": "negative",
                        "title": "Monthly Cash Deficit",
                        "description": f"Expenditures exceed income by {target_currency} {abs(net):,.2f}.",
                        "calculation": f"Income ({inc:,.2f}) - Expenses ({exp:,.2f}) = Deficit ({net:,.2f}).",
                        "is_fact": True,
                    }
                )

        # 2. Month-over-Month Spending Acceleration
        trends = self.calculate_monthly_trends(
            transactions, currency=target_currency, months_count=3
        )
        if len(trends) >= 2:
            prev_exp = trends[-2]["expense"]
            curr_exp = trends[-1]["expense"]
            if prev_exp > Decimal("0.00") and curr_exp > prev_exp:
                delta = curr_exp - prev_exp
                delta_pct = (delta / prev_exp * Decimal("100.00")).quantize(Decimal("0.1"))
                if delta_pct >= Decimal("15.0"):
                    insights.append(
                        {
                            "category": "SPENDING_TREND",
                            "severity": "warning",
                            "title": "Spending Acceleration Detected",
                            "description": f"Expenses increased by {delta_pct}% ({target_currency} {delta:,.2f}) compared to the previous month.",
                            "calculation": f"Current ({curr_exp:,.2f}) vs Previous ({prev_exp:,.2f}) = +{delta_pct}%.",
                            "is_fact": True,
                        }
                    )

        # 3. Budget Threshold Warnings
        if budgets and utilizations:
            b_results = self.calculate_budget_vs_actual(budgets, utilizations)
            for b in b_results:
                if b["is_overspent"]:
                    insights.append(
                        {
                            "category": "BUDGET",
                            "severity": "negative",
                            "title": f"Budget Cap Exceeded: {b['category_name']}",
                            "description": f"Spending in '{b['category_name']}' is {b['utilization_percentage']}% of limit (exceeded by {target_currency} {abs(b['remaining_amount']):,.2f}).",
                            "calculation": f"Spent ({b['spent_amount']:,.2f}) vs Budget ({b['budgeted_amount']:,.2f}).",
                            "is_fact": True,
                        }
                    )
                elif b["status"] == "WARNING":
                    insights.append(
                        {
                            "category": "BUDGET",
                            "severity": "warning",
                            "title": f"Budget Near Cap: {b['category_name']}",
                            "description": f"Spending in '{b['category_name']}' has reached {b['utilization_percentage']}% of your monthly cap.",
                            "calculation": f"Spent ({b['spent_amount']:,.2f}) of ({b['budgeted_amount']:,.2f}) cap.",
                            "is_fact": True,
                        }
                    )

        # 4. Savings Milestones Progress
        if goals:
            g_results = self.calculate_savings_progress(goals)
            for g in g_results:
                if g["is_achieved"]:
                    insights.append(
                        {
                            "category": "SAVINGS",
                            "severity": "positive",
                            "title": f"Milestone Achieved: {g['name']}",
                            "description": f"Target of {g['currency']} {g['target_amount']:,.2f} has been fully funded!",
                            "calculation": f"Current balance ({g['current_amount']:,.2f}) >= Target ({g['target_amount']:,.2f}).",
                            "is_fact": True,
                        }
                    )
                elif g["progress_percentage"] >= 75.0:
                    insights.append(
                        {
                            "category": "SAVINGS",
                            "severity": "accent",
                            "title": f"Milestone in Reach: {g['name']}",
                            "description": f"You have funded {g['progress_percentage']}% of your '{g['name']}' target.",
                            "calculation": f"{g['currency']} {g['remaining_amount']:,.2f} remaining to reach {g['currency']} {g['target_amount']:,.2f}.",
                            "is_fact": True,
                        }
                    )

        # 5. Due Recurring Obligations
        if recurring_rules:
            due_rules = [r for r in recurring_rules if r.get("is_active")]
            if due_rules:
                insights.append(
                    {
                        "category": "RECURRING",
                        "severity": "accent",
                        "title": f"Active Recurring Schedules ({len(due_rules)})",
                        "description": f"You have {len(due_rules)} active periodic recurring schedule template(s) configured.",
                        "calculation": "Derived from active RecurringRule records.",
                        "is_fact": True,
                    }
                )

        # 6. Debt Liabilities Status
        if loans:
            active_loans = [loan for loan in loans if not loan.get("is_settled")]
            total_debt = sum(
                [to_decimal(loan.get("remaining_balance", "0.00")) for loan in active_loans],
                Decimal("0.00"),
            )
            if active_loans and total_debt > Decimal("0.00"):
                insights.append(
                    {
                        "category": "DEBT",
                        "severity": "warning",
                        "title": f"Active Loan Obligations ({len(active_loans)})",
                        "description": f"Total outstanding loan principal balance across {len(active_loans)} active liability obligation(s) is {target_currency} {total_debt:,.2f}.",
                        "calculation": "Sum of remaining balances across active loans.",
                        "is_fact": True,
                    }
                )

        return insights


analytics_engine = FinancialAnalyticsEngine()
