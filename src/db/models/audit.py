"""SQLAlchemy model for Audit Logs."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, generate_uuid

if TYPE_CHECKING:
    from src.db.models.user import User


class AuditLog(Base):
    """Immutable audit log tracking financial state mutations."""

    __tablename__ = "audit_logs"

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
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    entity_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    old_values: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    new_values: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="audit_logs",
    )

    __table_args__ = (Index("ix_audit_logs_user_entity", "user_id", "entity_name", "created_at"),)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', entity='{self.entity_name}':{self.entity_id})>"
