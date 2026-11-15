"""Unit tests for RecurringService: schedule calculation, rule execution, and duplicate prevention."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from src.core.exceptions import ValidationError
from src.db.models.account import FinancialAccount
from src.db.models.category import Category, CategoryType
from src.db.models.recurring import Frequency
from src.db.models.transaction import TransactionType
from src.db.models.user import User
from src.schemas.recurring import RecurringRuleCreate
from src.services.recurring_service import RecurringService


@pytest.fixture
def utility_cat(db_session: Session, sample_user: User) -> Category:
    """Fixture providing an expense category."""
    cat = Category(
        user_id=sample_user.id,
        name="Electricity",
        category_type=CategoryType.EXPENSE,
    )
    db_session.add(cat)
    db_session.flush()
    return cat


def test_calculate_next_occurrence_all_frequencies() -> None:
    """Verify next occurrence date calculations across all frequencies."""
    start = date(2026, 1, 15)

    # Daily: interval=1 -> 2026-01-16
    assert RecurringService.calculate_next_occurrence(start, Frequency.DAILY, 1) == date(
        2026, 1, 16
    )
    # Daily: interval=3 -> 2026-01-18
    assert RecurringService.calculate_next_occurrence(start, Frequency.DAILY, 3) == date(
        2026, 1, 18
    )

    # Weekly: interval=1 -> 2026-01-22
    assert RecurringService.calculate_next_occurrence(start, Frequency.WEEKLY, 1) == date(
        2026, 1, 22
    )

    # Biweekly: interval=1 -> 2026-01-29
    assert RecurringService.calculate_next_occurrence(start, Frequency.BIWEEKLY, 1) == date(
        2026, 1, 29
    )

    # Monthly: interval=1 -> 2026-02-15
    assert RecurringService.calculate_next_occurrence(start, Frequency.MONTHLY, 1) == date(
        2026, 2, 15
    )

    # Monthly clamped on end of month: Jan 31 -> Feb 28
    jan31 = date(2026, 1, 31)
    assert RecurringService.calculate_next_occurrence(jan31, Frequency.MONTHLY, 1) == date(
        2026, 2, 28
    )

    # Quarterly: interval=1 -> 2026-04-15
    assert RecurringService.calculate_next_occurrence(start, Frequency.QUARTERLY, 1) == date(
        2026, 4, 15
    )

    # Yearly: interval=1 -> 2027-01-15
    assert RecurringService.calculate_next_occurrence(start, Frequency.YEARLY, 1) == date(
        2027, 1, 15
    )


def test_create_recurring_rule_success(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
    utility_cat: Category,
) -> None:
    """Verify creating a recurring rule."""
    service = RecurringService(db_session)
    payload = RecurringRuleCreate(
        name="Internet Bill",
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("1200.00"),
        currency="INR",
        frequency=Frequency.MONTHLY,
        interval=1,
        start_date=date(2026, 11, 1),
        category_id=utility_cat.id,
        account_id=sample_account.id,
    )
    rule = service.create_rule(sample_user.id, payload)
    assert rule.id is not None
    assert rule.name == "Internet Bill"
    assert rule.amount == Decimal("1200.00")
    assert rule.next_occurrence == date(2026, 11, 1)
    assert rule.is_active is True


def test_create_recurring_rule_validation_fails(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
) -> None:
    """Verify validation failures: non-positive amount and invalid dates."""
    service = RecurringService(db_session)

    # Non-positive amount
    with pytest.raises((ValidationError, PydanticValidationError)):
        service.create_rule(
            sample_user.id,
            RecurringRuleCreate(
                name="Bad Rule",
                transaction_type=TransactionType.EXPENSE,
                amount=Decimal("0.00"),
                frequency=Frequency.MONTHLY,
                start_date=date(2026, 11, 1),
                account_id=sample_account.id,
            ),
        )

    # End date before start date
    with pytest.raises((ValidationError, PydanticValidationError)) as exc:
        service.create_rule(
            sample_user.id,
            RecurringRuleCreate(
                name="Bad Dates",
                transaction_type=TransactionType.EXPENSE,
                amount=Decimal("500.00"),
                frequency=Frequency.MONTHLY,
                start_date=date(2026, 11, 10),
                end_date=date(2026, 11, 5),
                account_id=sample_account.id,
            ),
        )
    assert "end date cannot be earlier" in str(exc.value)


def test_execute_due_rules_and_duplicate_prevention(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
    utility_cat: Category,
) -> None:
    """Verify executing due rules spawns a transaction, advances next_date, and prevents duplicates."""
    service = RecurringService(db_session)
    rule = service.create_rule(
        sample_user.id,
        RecurringRuleCreate(
            name="Electricity Bill",
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("1500.00"),
            currency="INR",
            frequency=Frequency.MONTHLY,
            interval=1,
            start_date=date(2026, 11, 1),
            category_id=utility_cat.id,
            account_id=sample_account.id,
        ),
    )

    # Find due rules on 2026-11-05
    due = service.list_due_rules(sample_user.id, as_of_date=date(2026, 11, 5))
    assert len(due) == 1
    assert due[0].id == rule.id

    # Execute rule for date 2026-11-01
    tx = service.execute_due_rule(sample_user.id, rule.id, execution_date=date(2026, 11, 1))
    assert tx.id is not None
    assert tx.amount == Decimal("1500.00")
    assert tx.transaction_type == TransactionType.EXPENSE

    # Rule's next_occurrence should have advanced to 2026-12-01
    rule_updated = service.recurring_repo.get_by_id(rule.id, sample_user.id)
    assert rule_updated is not None
    assert rule_updated.next_occurrence == date(2026, 12, 1)

    # Attempting to execute again for the same date 2026-11-01 should fail
    with pytest.raises(ValidationError) as exc:
        service.execute_due_rule(sample_user.id, rule.id, execution_date=date(2026, 11, 1))
    assert "already spawned a transaction" in exc.value.message


def test_pause_and_resume_rule(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
    utility_cat: Category,
) -> None:
    """Verify pausing and resuming a recurring schedule."""
    service = RecurringService(db_session)
    rule = service.create_rule(
        sample_user.id,
        RecurringRuleCreate(
            name="Gym Membership",
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("2000.00"),
            frequency=Frequency.MONTHLY,
            start_date=date(2026, 11, 1),
            category_id=utility_cat.id,
            account_id=sample_account.id,
        ),
    )
    assert rule.is_active is True

    # Pause
    paused = service.pause_rule(sample_user.id, rule.id)
    assert paused.is_active is False

    # Resume
    resumed = service.resume_rule(sample_user.id, rule.id)
    assert resumed.is_active is True
