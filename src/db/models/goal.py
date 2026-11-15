"""SQLAlchemy model for Savings Goals."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from src.db.models.user import User


class SavingsGoal(Base, TimestampMixin):
    """SavingsGoal entity tracking user targets and progress."""

    __tablename__ = "savings_goals"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )
    target_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_achieved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="savings_goals",
    )

    __table_args__ = (
        Index("ix_savings_goals_user_achieved", "user_id", "is_achieved"),
        CheckConstraint("target_amount > 0", name="chk_savings_goals_positive_target"),
        CheckConstraint("current_amount >= 0", name="chk_savings_goals_non_negative_current"),
    )

    def __repr__(self) -> str:
        return f"<SavingsGoal(id={self.id}, name='{self.name}', progress={self.current_amount}/{self.target_amount})>"
