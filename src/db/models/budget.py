"""SQLAlchemy model for Budgets."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from src.db.models.category import Category
    from src.db.models.user import User


class Budget(Base, TimestampMixin):
    """Budget entity establishing monthly spending allocations for categories."""

    __tablename__ = "budgets"

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
    category_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    rollover_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    notes: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="budgets",
    )
    category: Mapped["Category"] = relationship(
        back_populates="budgets",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "category_id", "month", "year", name="uq_budgets_user_cat_period"
        ),
        Index("ix_budgets_user_period", "user_id", "year", "month"),
        CheckConstraint("month >= 1 AND month <= 12", name="chk_budgets_valid_month"),
        CheckConstraint("amount > 0", name="chk_budgets_positive_amount"),
    )

    def __repr__(self) -> str:
        return f"<Budget(id={self.id}, user_id={self.user_id}, category_id={self.category_id}, {self.year}-{self.month:02d}: {self.amount})>"
