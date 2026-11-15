"""Repository layer for Recurring Transaction Rules."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.recurring import Frequency, RecurringRule
from src.db.models.transaction import Transaction, TransactionType


class RecurringRepository:
    """Encapsulates database operations for RecurringRule entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: str,
        account_id: str,
        name: str,
        amount: Decimal,
        currency: str,
        transaction_type: TransactionType,
        frequency: Frequency,
        interval: int,
        start_date: date,
        end_date: date | None = None,
        category_id: str | None = None,
        destination_account_id: str | None = None,
        notes: str | None = None,
    ) -> RecurringRule:
        """Create and persist a new recurring transaction rule."""
        rule = RecurringRule(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            destination_account_id=destination_account_id,
            name=name,
            amount=amount,
            currency=currency,
            transaction_type=transaction_type,
            frequency=frequency,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            next_occurrence=start_date,
            is_active=True,
            notes=notes,
        )
        self.session.add(rule)
        self.session.flush()
        return rule

    def get_by_id(self, rule_id: str, user_id: str) -> RecurringRule | None:
        """Fetch recurring rule by ID, scoped to user."""
        stmt = select(RecurringRule).where(
            RecurringRule.id == rule_id,
            RecurringRule.user_id == user_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: str, active_only: bool = True) -> list[RecurringRule]:
        """Fetch recurring rules for user."""
        stmt = select(RecurringRule).where(RecurringRule.user_id == user_id)
        if active_only:
            stmt = stmt.where(RecurringRule.is_active.is_(True))
        stmt = stmt.order_by(RecurringRule.next_occurrence.asc())
        return list(self.session.execute(stmt).scalars().all())

    def list_due(self, as_of_date: date, user_id: str | None = None) -> list[RecurringRule]:
        """Fetch rules where next_occurrence <= as_of_date and is_active is True."""
        stmt = select(RecurringRule).where(
            RecurringRule.is_active.is_(True),
            RecurringRule.next_occurrence <= as_of_date,
        )
        if user_id:
            stmt = stmt.where(RecurringRule.user_id == user_id)
        stmt = stmt.order_by(RecurringRule.next_occurrence.asc())
        return list(self.session.execute(stmt).scalars().all())

    def find_existing_execution(self, rule_id: str, execution_date: date) -> Transaction | None:
        """Check if a transaction has already been spawned for this rule on the specific date."""
        stmt = select(Transaction).where(
            Transaction.recurring_rule_id == rule_id,
            Transaction.transaction_date == execution_date,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def update(self, rule: RecurringRule) -> RecurringRule:
        """Flush changes to recurring rule."""
        self.session.flush()
        return rule
