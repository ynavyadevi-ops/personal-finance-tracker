"""Unit tests for PrivacySafeAiInsightsService: de-identification, opt-in boundaries, and disclaimers."""

from decimal import Decimal

from src.services.ai_insights import PrivacySafeAiInsightsService


def test_ai_disabled_by_default() -> None:
    """Verify AI narrative returns privacy prompt and is disabled by default."""
    service = PrivacySafeAiInsightsService()
    metrics = {
        "currency": "INR",
        "monthly_income_band": "50000.00",
        "monthly_expense_band": "30000.00",
    }

    res = service.generate_ai_narrative(metrics, user_opted_in=False)
    assert res["is_enabled"] is False
    assert "disabled by default" in res["summary"]
    assert "Zero account numbers" in res["data_shared_disclosure"]


def test_ai_opt_in_consent_generates_narrative() -> None:
    """Verify enabling AI consent synthesizes cash flow narrative with disclaimer."""
    service = PrivacySafeAiInsightsService()
    metrics = {
        "currency": "INR",
        "monthly_income_band": "60000.00",
        "monthly_expense_band": "40000.00",
        "net_cash_flow": "20000.00",
        "savings_rate_pct": 33.3,
        "top_expense_proportions": [{"category": "Housing", "percentage": 50.0}],
    }

    res = service.generate_ai_narrative(metrics, user_opted_in=True)
    assert res["is_enabled"] is True
    assert "healthy surplus of INR 20,000.00" in res["summary"]
    assert "Housing" in res["summary"]
    assert "do not constitute certified or regulated financial advice" in res["disclaimer"]


def test_payload_sanitization_strips_pii_and_credentials() -> None:
    """Verify sanitization produces only high-level aggregates without PII or raw descriptions."""
    service = PrivacySafeAiInsightsService()
    raw_cash_flow = {
        "total_income": Decimal("75000.00"),
        "total_expense": Decimal("45000.00"),
        "net_cash_flow": Decimal("30000.00"),
        "raw_user_email": "sensitive@user.dev",
        "jwt_token": "secret-bearer-token",
    }
    raw_categories = [
        {"category": "Groceries", "amount": Decimal("15000.00"), "percentage": 33.3},
        {"category": "Dining", "amount": Decimal("10000.00"), "percentage": 22.2},
    ]

    payload = service.sanitize_for_ai_payload(
        cash_flow=raw_cash_flow,
        category_spending=raw_categories,
        savings_rate=Decimal("40.0"),
        currency="INR",
    )

    # Asserts zero leakage of credentials or emails
    assert "raw_user_email" not in payload
    assert "jwt_token" not in payload
    assert payload["currency"] == "INR"
    assert payload["monthly_income_band"] == "75000.00"
    assert len(payload["top_expense_proportions"]) == 2
    assert payload["top_expense_proportions"][0]["category"] == "Groceries"
