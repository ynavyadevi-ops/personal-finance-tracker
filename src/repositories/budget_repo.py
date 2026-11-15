"""Repository layer for Budgets and category spending aggregation."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models.budget import Budget
from src.db.models.transaction import Transaction, TransactionEntry, TransactionType


class BudgetRepository:
    """Encapsulates database operations and spending aggregations for Budgets."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: str,
        category_id: str,
        month: int,
        year: int,
        amount: Decimal,
        rollover_enabled: bool = False,
        notes: str | None = None,
    ) -> Budget:
        """Create a monthly budget for a category."""
        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            month=month,
            year=year,
            amount=amount,
            rollover_enabled=rollover_enabled,
            notes=notes,
        )
        self.session.add(budget)
        self.session.flush()
        return budget

    def get_by_id(self, budget_id: str, user_id: str) -> Budget | None:
        """Fetch budget by ID with tenant scoping."""
        stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_period(self, user_id: str, category_id: str, month: int, year: int) -> Budget | None:
        """Fetch budget for specific category, month, and year."""
        stmt = select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.month == month,
            Budget.year == year,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_period(self, user_id: str, month: int, year: int) -> list[Budget]:
        """Fetch all category budgets for a specific period."""
        stmt = select(Budget).where(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.year == year,
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_category_monthly_spent(
        self, user_id: str, category_id: str, month: int, year: int
    ) -> Decimal:
        """Calculate total actual expenses spent in a category for a calendar month.

        Strictly excludes internal transfers (TransactionType.TRANSFER).
        """
        start_date = date(year, month, 1)
        # Compute end of month
        if month == 12:
            end_date = date(year, 12, 31)
        else:
            # First day of next month minus 1 day
            import calendar

            _, last_day = calendar.monthrange(year, month)
            end_date = date(year, month, last_day)

        stmt = (
            select(func.coalesce(func.sum(TransactionEntry.amount), 0))
            .join(TransactionEntry.transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == TransactionType.EXPENSE,
                TransactionEntry.category_id == category_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
        )
        result = self.session.execute(stmt).scalar()
        return Decimal(str(result or "0.00"))
