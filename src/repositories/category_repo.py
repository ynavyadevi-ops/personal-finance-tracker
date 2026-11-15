"""Repository layer for Categories."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.db.models.category import Category, CategoryType


class CategoryRepository:
    """Encapsulates database operations for Category entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, category_id: str) -> Category | None:
        """Fetch a category by ID."""
        stmt = select(Category).where(Category.id == category_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_user_accessible_category(self, category_id: str, user_id: str) -> Category | None:
        """Fetch category, verifying it is either owned by the user or a global default."""
        stmt = select(Category).where(
            Category.id == category_id,
            or_(Category.user_id == user_id, Category.user_id.is_(None)),
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_user(
        self,
        user_id: str,
        category_type: CategoryType | None = None,
        include_defaults: bool = True,
    ) -> list[Category]:
        """List categories available to user (personal + optional global defaults)."""
        conditions = [Category.user_id == user_id]
        if include_defaults:
            conditions.append(Category.user_id.is_(None))

        stmt = select(Category).where(or_(*conditions))
        if category_type:
            stmt = stmt.where(Category.category_type == category_type)

        stmt = stmt.order_by(Category.name.asc())
        return list(self.session.execute(stmt).scalars().all())

    def create(
        self,
        user_id: str,
        name: str,
        category_type: CategoryType,
        parent_id: str | None = None,
        color: str = "#10b981",
        icon: str | None = None,
        is_default: bool = False,
    ) -> Category:
        """Create and persist a new category."""
        cat = Category(
            user_id=user_id,
            name=name,
            category_type=category_type,
            parent_id=parent_id,
            color=color,
            icon=icon,
            is_default=is_default,
        )
        self.session.add(cat)
        self.session.flush()
        return cat
