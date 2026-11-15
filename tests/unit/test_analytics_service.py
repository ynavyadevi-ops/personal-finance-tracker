"""Unit tests for FinancialAnalyticsEngine: cash flow, category breakdowns, trends, and rule-based insights."""

from decimal import Decimal

from src.services.analytics_service import FinancialAnalyticsEngine


def test_cash_flow_calculation_excludes_transfers_and_reversals() -> None:
    """Verify transfers and reversals are strictly excluded from income and expenses."""
    engine = FinancialAnalyticsEngine()
    transactions = [
        {
            "id": "tx-1",
            "transaction_type": "INCOME",
            "amount": "50000.00",
            "currency": "INR",
            "transaction_date": "2026-11-01",
            "description": "Salary",
        },
        {
            "id": "tx-2",
            "transaction_type": "EXPENSE",
            "amount": "15000.00",
            "currency": "INR",
            "transaction_date": "2026-11-02",
            "description": "Rent",
        },
        {
            "id": "tx-3",
            "transaction_type": "TRANSFER",
            "amount": "10000.00",
            "currency": "INR",
            "transaction_date": "2026-11-03",
            "description": "Transfer to Savings",
        },
        {
            "id": "tx-4",
            "transaction_type": "EXPENSE",
            "amount": "5000.00",
            "currency": "INR",
            "transaction_date": "2026-11-04",
            "description": "Reversal of accidental charge",
        },
        {
            "id": "tx-5",
            "transaction_type": "INCOME",
            "amount": "1000.00",
            "currency": "USD",
            "transaction_date": "2026-11-05",
            "description": "USD Dividend",
        },
    ]

    result = engine.calculate_cash_flow(transactions, currency="INR")
    assert result["currency"] == "INR"
    assert result["total_income"] == Decimal("50000.00")
    assert result["total_expense"] == Decimal("15000.00")
    assert result["net_cash_flow"] == Decimal("35000.00")
    assert result["savings_rate_pct"] == Decimal("70.00")
    assert result["transaction_count"] == 2


def test_spending_by_category_calculation() -> None:
    """Verify category expense rollups and proportional percentages."""
    engine = FinancialAnalyticsEngine()
    transactions = [
        {
            "transaction_type": "EXPENSE",
            "amount": "6000.00",
            "currency": "INR",
            "category": "Groceries",
        },
        {
            "transaction_type": "EXPENSE",
            "amount": "4000.00",
            "currency": "INR",
            "category": "Utilities",
        },
        {
            "transaction_type": "EXPENSE",
            "amount": "10000.00",
            "currency": "INR",
            "category": "Rent",
        },
        {
            "transaction_type": "TRANSFER",
            "amount": "5000.00",
            "currency": "INR",
            "category": "Transfer",
        },
    ]

    breakdown = engine.calculate_spending_by_category(transactions, currency="INR")
    assert len(breakdown) == 3
    assert breakdown[0]["category"] == "Rent"
    assert breakdown[0]["amount"] == Decimal("10000.00")
    assert breakdown[0]["percentage"] == 50.0

    assert breakdown[1]["category"] == "Groceries"
    assert breakdown[1]["percentage"] == 30.0

    assert breakdown[2]["category"] == "Utilities"
    assert breakdown[2]["percentage"] == 20.0


def test_monthly_trends_calculation() -> None:
    """Verify month-by-month income, expense, and net cash flow trajectory."""
    engine = FinancialAnalyticsEngine()
    transactions = [
        {
            "transaction_type": "INCOME",
            "amount": "40000.00",
            "currency": "INR",
            "transaction_date": "2026-09-10",
        },
        {
            "transaction_type": "EXPENSE",
            "amount": "25000.00",
            "currency": "INR",
            "transaction_date": "2026-09-15",
        },
        {
            "transaction_type": "INCOME",
            "amount": "45000.00",
            "currency": "INR",
            "transaction_date": "2026-10-10",
        },
        {
            "transaction_type": "EXPENSE",
            "amount": "30000.00",
            "currency": "INR",
            "transaction_date": "2026-10-20",
        },
    ]

    trends = engine.calculate_monthly_trends(transactions, currency="INR", months_count=6)
    assert len(trends) == 2
    assert trends[0]["month"] == "2026-09"
    assert trends[0]["income"] == Decimal("40000.00")
    assert trends[0]["expense"] == Decimal("25000.00")
    assert trends[0]["net_flow"] == Decimal("15000.00")

    assert trends[1]["month"] == "2026-10"
    assert trends[1]["net_flow"] == Decimal("15000.00")


def test_account_balance_distribution() -> None:
    """Verify account balance distribution respects currency isolation."""
    engine = FinancialAnalyticsEngine()
    accounts = [
        {"id": "acc-1", "name": "Salary Account", "currency": "INR", "current_balance": "60000.00"},
        {
            "id": "acc-2",
            "name": "Savings Account",
            "currency": "INR",
            "current_balance": "40000.00",
        },
        {"id": "acc-3", "name": "USD Brokerage", "currency": "USD", "current_balance": "5000.00"},
    ]

    dist = engine.calculate_account_balance_distribution(accounts, currency="INR")
    assert len(dist) == 2
    assert dist[0]["name"] == "Salary Account"
    assert dist[0]["percentage"] == 60.0
    assert dist[1]["name"] == "Savings Account"
    assert dist[1]["percentage"] == 40.0


def test_budget_vs_actual_status() -> None:
    """Verify budget reconciliations flag warnings at 80% and overspent status at 100%."""
    engine = FinancialAnalyticsEngine()
    budgets = [
        {"category_id": "cat-1", "amount": "10000.00"},
        {"category_id": "cat-2", "amount": "5000.00"},
        {"category_id": "cat-3", "amount": "8000.00"},
    ]
    utilizations = [
        {"category_id": "cat-1", "category_name": "Groceries", "spent_amount": "8500.00"},
        {"category_id": "cat-2", "category_name": "Dining", "spent_amount": "6000.00"},
        {"category_id": "cat-3", "category_name": "Utilities", "spent_amount": "4000.00"},
    ]

    results = engine.calculate_budget_vs_actual(budgets, utilizations)
    res_map = {r["category_id"]: r for r in results}

    assert res_map["cat-1"]["status"] == "WARNING"
    assert res_map["cat-1"]["is_overspent"] is False

    assert res_map["cat-2"]["status"] == "EXCEEDED"
    assert res_map["cat-2"]["is_overspent"] is True

    assert res_map["cat-3"]["status"] == "NORMAL"
    assert res_map["cat-3"]["is_overspent"] is False


def test_savings_progress_calculation() -> None:
    """Verify savings milestone progress calculation and achievement flags."""
    engine = FinancialAnalyticsEngine()
    goals = [
        {
            "id": "g-1",
            "name": "Emergency Fund",
            "target_amount": "100000.00",
            "current_amount": "100000.00",
            "currency": "INR",
        },
        {
            "id": "g-2",
            "name": "Vacation Fund",
            "target_amount": "50000.00",
            "current_amount": "25000.00",
            "currency": "INR",
        },
    ]

    res = engine.calculate_savings_progress(goals)
    assert len(res) == 2
    assert res[0]["is_achieved"] is True
    assert res[0]["progress_percentage"] == 100.0

    assert res[1]["is_achieved"] is False
    assert res[1]["remaining_amount"] == Decimal("25000.00")
    assert res[1]["progress_percentage"] == 50.0


def test_investment_cost_basis_summary() -> None:
    """Verify portfolio acquisition cost basis summaries and disclaimer."""
    engine = FinancialAnalyticsEngine()
    holdings = [
        {
            "asset_id": "a-1",
            "quantity": "10.0000",
            "total_cost": "25000.00",
            "cost_basis_per_unit": "2500.00",
            "currency": "INR",
            "asset": {"symbol": "RELIANCE", "name": "Reliance Industries"},
        },
        {
            "asset_id": "a-2",
            "quantity": "20.0000",
            "total_cost": "75000.00",
            "cost_basis_per_unit": "3750.00",
            "currency": "INR",
            "asset": {"symbol": "TCS", "name": "Tata Consultancy Services"},
        },
    ]

    summary = engine.calculate_investment_cost_basis_summary(holdings, currency="INR")
    assert summary["total_invested_cost"] == Decimal("100000.00")
    assert summary["positions_count"] == 2
    assert summary["positions"][0]["symbol"] == "TCS"
    assert summary["positions"][0]["allocation_pct"] == 75.0
    assert "historical acquisition costs" in summary["valuation_disclaimer"].lower()


def test_generate_rule_based_insights() -> None:
    """Verify rule-based deterministic insights generate explainable calculations."""
    engine = FinancialAnalyticsEngine()
    transactions = [
        {
            "transaction_type": "INCOME",
            "amount": "100000.00",
            "currency": "INR",
            "transaction_date": "2026-11-01",
        },
        {
            "transaction_type": "EXPENSE",
            "amount": "40000.00",
            "currency": "INR",
            "transaction_date": "2026-11-05",
        },
    ]
    budgets = [{"category_id": "c-1", "amount": "10000.00"}]
    utilizations = [{"category_id": "c-1", "category_name": "Shopping", "spent_amount": "12000.00"}]
    goals = [
        {
            "name": "House Downpayment",
            "target_amount": "500000.00",
            "current_amount": "400000.00",
            "currency": "INR",
        }
    ]
    loans = [
        {"lender_name": "Bank of India", "remaining_balance": "250000.00", "is_settled": False}
    ]

    insights = engine.generate_rule_based_insights(
        transactions=transactions,
        budgets=budgets,
        utilizations=utilizations,
        goals=goals,
        loans=loans,
        currency="INR",
    )

    categories = [i["category"] for i in insights]
    assert "CASH_FLOW" in categories
    assert "BUDGET" in categories
    assert "SAVINGS" in categories
    assert "DEBT" in categories

    # All insights must explain their derivation
    for item in insights:
        assert "calculation" in item
        assert len(item["calculation"]) > 0
        assert item["is_fact"] is True
