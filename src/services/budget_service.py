"""Domain service implementing business rules for Budgets, Category Spending, and Rollover."""

from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError, ValidationError
from src.core.logging import logger
from src.core.money import to_decimal
from src.db.models.category import CategoryType
from src.repositories.budget_repo import BudgetRepository
from src.repositories.category_repo import CategoryRepository
from src.schemas.budget import BudgetCreate, BudgetRead, BudgetUtilization


class BudgetService:
    """Orchestrates budget allocations, monthly expenditure aggregations, and visual thresholds."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.budget_repo = BudgetRepository(session)
        self.category_repo = CategoryRepository(session)

    def set_budget(self, user_id: str, payload: BudgetCreate) -> BudgetRead:
        """Create or update a monthly category budget allocation."""
        amt = to_decimal(payload.amount)
        if amt <= Decimal("0.00"):
            raise ValidationError("Budget amount must be strictly positive.")

        # 1. Validate category ownership and type
        category = self.category_repo.get_user_accessible_category(
            category_id=payload.category_id, user_id=user_id
        )
        if not category:
            raise NotFoundError(f"Category with ID '{payload.category_id}' was not found.")
        if category.category_type != CategoryType.EXPENSE:
            raise ValidationError(
                f"Budgets can only be assigned to EXPENSE categories, but '{category.name}' is an {category.category_type.value} category."
            )

        # 2. Check for existing budget for period
        existing = self.budget_repo.get_by_period(
            user_id=user_id,
            category_id=payload.category_id,
            month=payload.month,
            year=payload.year,
        )

        if existing:
            existing.amount = amt
            existing.rollover_enabled = payload.rollover_enabled
            if payload.notes is not None:
                existing.notes = payload.notes
            self.session.commit()
            self.session.refresh(existing)
            logger.info(
                f"Budget updated for category {category.name} ({payload.year}-{payload.month:02d})"
            )
            return BudgetRead.model_validate(existing)

        budget = self.budget_repo.create(
            user_id=user_id,
            category_id=payload.category_id,
            month=payload.month,
            year=payload.year,
            amount=amt,
            rollover_enabled=payload.rollover_enabled,
            notes=payload.notes,
        )
        self.session.commit()
        self.session.refresh(budget)
        logger.info(
            f"Budget created for category {category.name} ({payload.year}-{payload.month:02d}): ₹{amt}"
        )
        return BudgetRead.model_validate(budget)

    def get_budget_utilization(
        self, user_id: str, category_id: str, month: int, year: int
    ) -> BudgetUtilization:
        """Calculate consumption, remaining balance, rollover, and status thresholds."""
        budget = self.budget_repo.get_by_period(
            user_id=user_id, category_id=category_id, month=month, year=year
        )
        if not budget:
            raise NotFoundError(
                f"No budget configured for category '{category_id}' in period {year}-{month:02d}."
            )

        category = self.category_repo.get_by_id(category_id)
        cat_name = category.name if category else "Unknown Category"

        # 1. Aggregate actual monthly expenses (internal transfers strictly excluded)
        spent = self.budget_repo.get_category_monthly_spent(
            user_id=user_id, category_id=category_id, month=month, year=year
        )

        # 2. Compute optional rollover from previous month if enabled
        rollover_amount = Decimal("0.00")
        if budget.rollover_enabled:
            prev_month = 12 if month == 1 else month - 1
            prev_year = year - 1 if month == 1 else year
            prev_budget = self.budget_repo.get_by_period(
                user_id=user_id, category_id=category_id, month=prev_month, year=prev_year
            )
            if prev_budget:
                prev_spent = self.budget_repo.get_category_monthly_spent(
                    user_id=user_id, category_id=category_id, month=prev_month, year=prev_year
                )
                unspent = prev_budget.amount - prev_spent
                if unspent > Decimal("0.00"):
                    rollover_amount = to_decimal(unspent)

        effective_budget = to_decimal(budget.amount) + rollover_amount
        remaining_amount = effective_budget - spent
        is_overspent = spent > effective_budget

        if effective_budget > Decimal("0.00"):
            util_pct = to_decimal((spent / effective_budget) * Decimal("100.00"))
        else:
            util_pct = Decimal("100.00")

        # Threshold status: NORMAL (<80%), WARNING (80-99.99%), EXCEEDED (>=100%)
        if spent >= effective_budget:
            status = "EXCEEDED"
        elif util_pct >= Decimal("80.00"):
            status = "WARNING"
        else:
            status = "NORMAL"

        return BudgetUtilization(
            budget_id=budget.id,
            category_id=category_id,
            category_name=cat_name,
            month=month,
            year=year,
            budgeted_amount=to_decimal(budget.amount),
            spent_amount=to_decimal(spent),
            remaining_amount=to_decimal(remaining_amount),
            utilization_percentage=util_pct,
            is_overspent=is_overspent,
            status=status,
            rollover_amount=rollover_amount,
        )

    def list_budget_utilizations(
        self, user_id: str, month: int, year: int
    ) -> list[BudgetUtilization]:
        """Fetch utilization metrics for all budgets defined for a period."""
        budgets = self.budget_repo.list_by_period(user_id=user_id, month=month, year=year)
        results = []
        for b in budgets:
            util = self.get_budget_utilization(
                user_id=user_id, category_id=b.category_id, month=month, year=year
            )
            results.append(util)
        return results
