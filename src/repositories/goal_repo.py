"""Repository layer for SavingsGoals."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.goal import SavingsGoal


class SavingsGoalRepository:
    """Encapsulates database operations for SavingsGoal entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: str,
        name: str,
        target_amount: Decimal,
        currency: str = "INR",
        target_date: date | None = None,
        notes: str | None = None,
    ) -> SavingsGoal:
        """Create and persist a new savings goal."""
        goal = SavingsGoal(
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            current_amount=Decimal("0.00"),
            currency=currency,
            target_date=target_date,
            is_achieved=False,
            notes=notes,
        )
        self.session.add(goal)
        self.session.flush()
        return goal

    def get_by_id(self, goal_id: str, user_id: str) -> SavingsGoal | None:
        """Fetch savings goal by ID, scoped to user."""
        stmt = select(SavingsGoal).where(
            SavingsGoal.id == goal_id,
            SavingsGoal.user_id == user_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: str) -> list[SavingsGoal]:
        """Fetch all savings goals for a user."""
        stmt = select(SavingsGoal).where(SavingsGoal.user_id == user_id)
        stmt = stmt.order_by(SavingsGoal.is_achieved.asc(), SavingsGoal.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def update(self, goal: SavingsGoal) -> SavingsGoal:
        """Flush changes to a goal."""
        self.session.flush()
        return goal
