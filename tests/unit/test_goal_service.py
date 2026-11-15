"""Unit tests for SavingsGoalService: goal creation, contributions, withdrawals, and progress."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError, ValidationError
from src.db.models.user import User
from src.schemas.goal import SavingsGoalCreate
from src.services.goal_service import SavingsGoalService


def test_create_goal_success(db_session: Session, sample_user: User) -> None:
    """Verify creating a savings goal."""
    service = SavingsGoalService(db_session)
    payload = SavingsGoalCreate(
        name="Emergency Fund",
        target_amount=Decimal("100000.00"),
        currency="INR",
        target_date=date(2027, 12, 31),
        notes="6 months living expenses",
    )
    goal = service.create_goal(sample_user.id, payload)
    assert goal.id is not None
    assert goal.name == "Emergency Fund"
    assert goal.target_amount == Decimal("100000.00")
    assert goal.current_amount == Decimal("0.00")
    assert goal.is_achieved is False


def test_create_goal_invalid_target_fails(db_session: Session, sample_user: User) -> None:
    """Verify non-positive target amount raises ValidationError."""
    service = SavingsGoalService(db_session)
    with pytest.raises((ValidationError, PydanticValidationError)):
        payload = SavingsGoalCreate(
            name="Invalid Goal",
            target_amount=Decimal("0.00"),
            currency="INR",
        )
        service.create_goal(sample_user.id, payload)


def test_add_contribution_success_and_achievement(db_session: Session, sample_user: User) -> None:
    """Verify adding contributions updates current amount and flags is_achieved when target reached."""
    service = SavingsGoalService(db_session)
    goal = service.create_goal(
        sample_user.id,
        SavingsGoalCreate(
            name="Laptop Fund",
            target_amount=Decimal("50000.00"),
        ),
    )

    # Partial contribution: ₹20,000 -> 40%
    prog1 = service.add_contribution(sample_user.id, goal.id, Decimal("20000.00"))
    assert prog1.current_amount == Decimal("20000.00")
    assert prog1.remaining_amount == Decimal("30000.00")
    assert prog1.progress_percentage == Decimal("40.00")
    assert prog1.is_achieved is False

    # Second contribution: ₹30,000 -> 100%, is_achieved = True
    prog2 = service.add_contribution(sample_user.id, goal.id, Decimal("30000.00"))
    assert prog2.current_amount == Decimal("50000.00")
    assert prog2.remaining_amount == Decimal("0.00")
    assert prog2.progress_percentage == Decimal("100.00")
    assert prog2.is_achieved is True


def test_withdraw_contribution_success(db_session: Session, sample_user: User) -> None:
    """Verify withdrawing savings decrements current amount and unsets is_achieved if dropping below target."""
    service = SavingsGoalService(db_session)
    goal = service.create_goal(
        sample_user.id,
        SavingsGoalCreate(
            name="Trip Fund",
            target_amount=Decimal("20000.00"),
        ),
    )
    service.add_contribution(sample_user.id, goal.id, Decimal("20000.00"))

    # Withdraw ₹5,000
    prog = service.withdraw_contribution(sample_user.id, goal.id, Decimal("5000.00"))
    assert prog.current_amount == Decimal("15000.00")
    assert prog.remaining_amount == Decimal("5000.00")
    assert prog.progress_percentage == Decimal("75.00")
    assert prog.is_achieved is False


def test_withdraw_more_than_current_fails(db_session: Session, sample_user: User) -> None:
    """Verify withdrawing more than current savings raises ValidationError."""
    service = SavingsGoalService(db_session)
    goal = service.create_goal(
        sample_user.id,
        SavingsGoalCreate(
            name="Bike Fund",
            target_amount=Decimal("10000.00"),
        ),
    )
    service.add_contribution(sample_user.id, goal.id, Decimal("2000.00"))

    with pytest.raises(ValidationError) as exc:
        service.withdraw_contribution(sample_user.id, goal.id, Decimal("3000.00"))
    assert "Cannot withdraw" in exc.value.message


def test_goal_not_found_raises(db_session: Session, sample_user: User) -> None:
    """Verify operations on missing goal ID raise NotFoundError."""
    service = SavingsGoalService(db_session)
    with pytest.raises(NotFoundError):
        service.get_goal_progress(sample_user.id, "missing-goal-id")
