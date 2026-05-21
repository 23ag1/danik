from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import AuditEntityType, IncidentStatus
from app.models.event import Event
from app.models.incident import Incident
from app.models.audit import AuditLog
from app.schemas.incident import IncidentRead, IncidentStatusUpdate

router = APIRouter(prefix="/incidents", tags=["incidents"])


class _IncidentWithText:
    __slots__ = (
        "id", "event_id", "title", "raw_text", "risk_score", "severity",
        "rule_score", "ml_score", "graph_score", "anomaly_score",
        "rule_flags", "status", "analyst_comment", "created_at", "updated_at",
    )

    def __init__(self, incident: Incident, raw_text: str) -> None:
        self.id = incident.id
        self.event_id = incident.event_id
        self.title = incident.title
        self.raw_text = raw_text
        self.risk_score = incident.risk_score
        self.severity = incident.severity
        self.rule_score = incident.rule_score
        self.ml_score = incident.ml_score
        self.graph_score = incident.graph_score
        self.anomaly_score = incident.anomaly_score
        self.rule_flags = incident.rule_flags
        self.status = incident.status
        self.analyst_comment = incident.analyst_comment
        self.created_at = incident.created_at
        self.updated_at = incident.updated_at


@router.get("", response_model=list[IncidentRead])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        select(Incident, Event.raw_text)
        .join(Event, Incident.event_id == Event.id)
        .order_by(Incident.created_at.desc())
    )
    return [_IncidentWithText(inc, raw_text) for inc, raw_text in rows.all()]


@router.patch("/{incident_id}/status", response_model=IncidentRead)
async def update_incident_status(
    incident_id: int,
    body: IncidentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    incident = await db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    old_status = incident.status
    incident.status = body.status
    if body.analyst_comment is not None:
        incident.analyst_comment = body.analyst_comment

    db.add(
        AuditLog(
            action="incident.status_updated",
            entity_type=AuditEntityType.incident,
            entity_id=incident.id,
            details={"old_status": old_status.value, "new_status": body.status.value},
        )
    )
    await db.commit()

    row = await db.execute(
        select(Incident, Event.raw_text)
        .join(Event, Incident.event_id == Event.id)
        .where(Incident.id == incident_id)
    )
    inc, raw_text = row.one()
    return _IncidentWithText(inc, raw_text)
