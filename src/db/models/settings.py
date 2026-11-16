"""SQLAlchemy model for System Settings."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class SystemSettings(Base):
    """Platform-wide system configuration settings."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )
    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<SystemSettings(key={self.key}, value={self.value})>"
