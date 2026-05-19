from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import AuditEntityType, IncidentStatus
from app.models.incident import Incident
from app.models.audit import AuditLog
from app.schemas.incident import IncidentRead, IncidentStatusUpdate

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentRead])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).order_by(Incident.created_at.desc()))
    return list(result.scalars().all())


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
    await db.refresh(incident)
    return incident
