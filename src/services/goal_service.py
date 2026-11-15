"""Domain service implementing business rules for Savings Goals and Milestone Progress."""

from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError, ValidationError
from src.core.logging import logger
from src.core.money import to_decimal
from src.repositories.goal_repo import SavingsGoalRepository
from src.schemas.goal import SavingsGoalCreate, SavingsGoalProgress, SavingsGoalRead


class SavingsGoalService:
    """Orchestrates savings goal targets, contribution tracking, and progress metrics."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.goal_repo = SavingsGoalRepository(session)

    def create_goal(self, user_id: str, payload: SavingsGoalCreate) -> SavingsGoalRead:
        """Create a new savings milestone target."""
        target = to_decimal(payload.target_amount)
        if target <= Decimal("0.00"):
            raise ValidationError("Savings goal target amount must be strictly positive.")

        goal = self.goal_repo.create(
            user_id=user_id,
            name=payload.name,
            target_amount=target,
            currency=payload.currency,
            target_date=payload.target_date,
            notes=payload.notes,
        )
        self.session.commit()
        self.session.refresh(goal)
        logger.info(f"Savings goal created: {goal.id} ({goal.name}) for ₹{target}")
        return SavingsGoalRead.model_validate(goal)

    def add_contribution(
        self, user_id: str, goal_id: str, amount: Decimal, notes: str | None = None
    ) -> SavingsGoalProgress:
        """Allocate funds towards a savings milestone."""
        contrib = to_decimal(amount)
        if contrib <= Decimal("0.00"):
            raise ValidationError("Savings goal contribution amount must be strictly positive.")

        goal = self.goal_repo.get_by_id(goal_id=goal_id, user_id=user_id)
        if not goal:
            raise NotFoundError(f"Savings goal with ID '{goal_id}' was not found.")

        goal.current_amount = to_decimal(goal.current_amount + contrib)
        if goal.current_amount >= goal.target_amount:
            goal.is_achieved = True

        self.session.commit()
        self.session.refresh(goal)
        logger.info(
            f"Contribution of ₹{contrib} added to goal '{goal.name}' (Current: ₹{goal.current_amount})"
        )
        return self.get_goal_progress(user_id=user_id, goal_id=goal_id)

    def withdraw_contribution(
        self, user_id: str, goal_id: str, amount: Decimal
    ) -> SavingsGoalProgress:
        """Withdraw allocated savings from a goal."""
        withdrawal = to_decimal(amount)
        if withdrawal <= Decimal("0.00"):
            raise ValidationError("Withdrawal amount must be strictly positive.")

        goal = self.goal_repo.get_by_id(goal_id=goal_id, user_id=user_id)
        if not goal:
            raise NotFoundError(f"Savings goal with ID '{goal_id}' was not found.")

        if withdrawal > goal.current_amount:
            raise ValidationError(
                f"Cannot withdraw ₹{withdrawal} from goal '{goal.name}' with current savings of ₹{goal.current_amount}."
            )

        goal.current_amount = to_decimal(goal.current_amount - withdrawal)
        if goal.current_amount < goal.target_amount:
            goal.is_achieved = False

        self.session.commit()
        self.session.refresh(goal)
        logger.info(
            f"Withdrawal of ₹{withdrawal} from goal '{goal.name}' (Current: ₹{goal.current_amount})"
        )
        return self.get_goal_progress(user_id=user_id, goal_id=goal_id)

    def get_goal_progress(self, user_id: str, goal_id: str) -> SavingsGoalProgress:
        """Compute progress percentage, remaining balance, and completion flag."""
        goal = self.goal_repo.get_by_id(goal_id=goal_id, user_id=user_id)
        if not goal:
            raise NotFoundError(f"Savings goal with ID '{goal_id}' was not found.")

        target = to_decimal(goal.target_amount)
        current = to_decimal(goal.current_amount)
        remaining = max(Decimal("0.00"), target - current)

        progress_pct = (
            to_decimal((current / target) * Decimal("100.00")) if target > 0 else Decimal("100.00")
        )

        return SavingsGoalProgress(
            goal_id=goal.id,
            name=goal.name,
            target_amount=target,
            current_amount=current,
            remaining_amount=remaining,
            progress_percentage=progress_pct,
            is_achieved=goal.is_achieved,
            currency=goal.currency,
        )

    def list_goals(self, user_id: str) -> list[SavingsGoalRead]:
        """Fetch all savings goals for a user."""
        goals = self.goal_repo.list_by_user(user_id=user_id)
        return [SavingsGoalRead.model_validate(g) for g in goals]
