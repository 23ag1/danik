from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, JSON, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.enums import AuditEntityType


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[AuditEntityType] = mapped_column(Enum(AuditEntityType))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor: Mapped[str] = mapped_column(String(64), default="system")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
