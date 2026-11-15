"""SQLAlchemy model for Categories."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from src.db.models.budget import Budget
    from src.db.models.transaction import TransactionEntry
    from src.db.models.user import User


class CategoryType(str, enum.Enum):
    """Classification of category flows."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class Category(Base, TimestampMixin):
    """Category entity for classifying financial transactions and budgets."""

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    category_type: Mapped[CategoryType] = mapped_column(
        SQLEnum(CategoryType, native_enum=False),
        nullable=False,
        default=CategoryType.EXPENSE,
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#10b981",
    )
    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # Relationships
    user: Mapped["User | None"] = relationship(
        back_populates="categories",
    )
    parent: Mapped["Category | None"] = relationship(
        "Category",
        remote_side=[id],
        back_populates="subcategories",
    )
    subcategories: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    transaction_entries: Mapped[list["TransactionEntry"]] = relationship(
        back_populates="category",
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_categories_user_name", "user_id", "name"),
        Index("ix_categories_type", "category_type"),
        UniqueConstraint("user_id", "name", "parent_id", name="uq_categories_user_name_parent"),
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name}, type={self.category_type})>"
