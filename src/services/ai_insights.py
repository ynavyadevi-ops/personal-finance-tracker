"""Privacy-conscious AI financial insights service with strict de-identification and opt-in boundaries."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


class PrivacySafeAiInsightsService:
    """Provides privacy-first AI insights generation.

    Enforces:
    - AI insights are disabled by default; requires explicit opt-in consent.
    - Zero personal identifiable information (PII), credentials, or account IDs in payloads.
    - Zero external network transfer without separate approval.
    - Strict de-identification using aggregated statistics and percentages only.
    - Clear disclaimers that AI observations are informational and not certified financial advice.
    """

    DEFAULT_DISCLAIMER = (
        "AI-assisted observations are generated for informational and planning purposes only, "
        "may contain inaccuracies, and do not constitute certified or regulated financial advice."
    )

    @classmethod
    def sanitize_for_ai_payload(
        cls,
        cash_flow: dict[str, Any],
        category_spending: list[dict[str, Any]],
        savings_rate: Decimal,
        currency: str = "INR",
    ) -> dict[str, Any]:
        """Strip all PII, account numbers, merchant names, and raw descriptions.

        Returns only high-level aggregate numbers and percentage allocations.
        """
        top_categories = []
        for c in category_spending[:5]:
            top_categories.append(
                {
                    "category": str(c.get("category", "General")),
                    "percentage": float(c.get("percentage", 0.0)),
                }
            )

        return {
            "currency": currency,
            "monthly_income_band": str(cash_flow.get("total_income", "0.00")),
            "monthly_expense_band": str(cash_flow.get("total_expense", "0.00")),
            "net_cash_flow": str(cash_flow.get("net_cash_flow", "0.00")),
            "savings_rate_pct": float(savings_rate),
            "top_expense_proportions": top_categories,
        }

    @classmethod
    def generate_ai_narrative(
        cls,
        aggregated_metrics: dict[str, Any],
        user_opted_in: bool = False,
    ) -> dict[str, Any]:
        """Generate privacy-safe synthesized observations when user has given consent."""
        if not user_opted_in:
            return {
                "is_enabled": False,
                "summary": "AI Financial Insights are disabled by default to safeguard your privacy. Enable the opt-in toggle in the Insights settings to view automated analytical observations.",
                "disclaimer": cls.DEFAULT_DISCLAIMER,
                "data_shared_disclosure": "When enabled, only high-level aggregate spending percentages and totals are processed. Zero account numbers, merchant names, emails, or personal identifiers are ever used.",
            }

        # Safe synthesized narrative generated deterministically from aggregated stats
        currency = aggregated_metrics.get("currency", "INR")
        net = Decimal(str(aggregated_metrics.get("net_cash_flow", "0.00")))
        savings_rate = float(aggregated_metrics.get("savings_rate_pct", 0.0))
        top_cats = aggregated_metrics.get("top_expense_proportions", [])

        narratives: list[str] = []

        if net > Decimal("0.00"):
            narratives.append(
                f"Your cash flow is in a healthy surplus of {currency} {net:,.2f}, resulting in a savings rate of {savings_rate:.1f}%. "
                "Consider directing surplus funds systematically toward existing savings milestones or principal debt reduction."
            )
        elif net < Decimal("0.00"):
            narratives.append(
                f"Expenditures currently exceed total income by {currency} {abs(net):,.2f}. "
                "Reviewing your top expenditure categories may reveal non-essential outlays that can be adjusted."
            )
        else:
            narratives.append(
                "Your cash flow is currently balanced at breakeven. Developing a liquid emergency reserve can help protect against unexpected expenses."
            )

        if top_cats:
            dominant = top_cats[0]
            narratives.append(
                f"Your largest expenditure concentration is in '{dominant['category']}', accounting for {dominant['percentage']:.1f}% of total outflows."
            )

        return {
            "is_enabled": True,
            "summary": " ".join(narratives),
            "disclaimer": cls.DEFAULT_DISCLAIMER,
            "data_shared_disclosure": "Processed locally using de-identified aggregate totals. Zero third-party cloud data transmission.",
        }


ai_insights_service = PrivacySafeAiInsightsService()
