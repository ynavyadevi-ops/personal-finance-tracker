"""Pydantic schemas for Category responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.db.models.category import CategoryType


class CategoryRead(BaseModel):
    """Schema for category responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None = None
    name: str
    category_type: CategoryType
    parent_id: str | None = None
    color: str = "#10b981"
    icon: str | None = None
    is_default: bool = False
    created_at: datetime | None = None
