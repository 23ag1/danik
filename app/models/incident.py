from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, DateTime, JSON, Integer, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.enums import Severity, IncidentStatus


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_event_id", "event_id"),
        Index("ix_incidents_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"))
    title: Mapped[str] = mapped_column(String(255))
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.low)
    rule_score: Mapped[float] = mapped_column(Float, default=0.0)
    ml_score: Mapped[float] = mapped_column(Float, default=0.0)
    graph_score: Mapped[float] = mapped_column(Float, default=0.0)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    rule_flags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.new)
    analyst_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
