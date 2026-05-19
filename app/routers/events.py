from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import AuditEntityType, Severity
from app.models.event import Event
from app.models.incident import Incident
from app.models.audit import AuditLog
from app.pipeline.graph_store import get_fraud_graph
from app.pipeline.scoring import compute_risk_score, risk_to_severity
from app.schemas.event import EventCreate, EventResponse
from app.services.pipeline_runner import process_event_text
from app.utils import hash_author

router = APIRouter(prefix="/events", tags=["events"])


def _incident_title(severity: Severity, rule_flags: list[str]) -> str:
    flag_hint = rule_flags[0] if rule_flags else "подозрительная активность"
    return f"[{severity.value}] {flag_hint}"


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(body: EventCreate, db: AsyncSession = Depends(get_db)):
    author_hash = hash_author(body.user_id)
    graph = get_fraud_graph()
    graph_score = graph.score_author(author_hash)

    processed = process_event_text(body.raw_text, graph_score=graph_score)
    detection = processed["detection"]

    graph_score = graph.register(
        author_hash,
        detection["rule_flags"],
        processed["risk_score"],
    )
    risk_score = compute_risk_score(
        rule_score=detection["rule_score"],
        ml_score=detection["ml_score"],
        graph_score=graph_score,
        anomaly_score=detection["anomaly_score"],
    )
    severity = risk_to_severity(risk_score)

    event = Event(
        source=body.source,
        author_hash=author_hash,
        raw_text=body.raw_text,
        clean_text=processed["clean_text"],
        url=body.url,
        meta=body.meta,
    )
    db.add(event)
    await db.flush()

    incident_id = None
    if severity != Severity.low:
        incident = Incident(
            event_id=event.id,
            title=_incident_title(severity, detection["rule_flags"]),
            risk_score=risk_score,
            severity=severity,
            rule_score=detection["rule_score"],
            ml_score=detection["ml_score"],
            graph_score=graph_score,
            rule_flags=detection["rule_flags"],
            anomaly_score=detection["anomaly_score"],
        )
        db.add(incident)
        await db.flush()
        incident_id = incident.id

        db.add(
            AuditLog(
                action="incident.created",
                entity_type=AuditEntityType.incident,
                entity_id=incident.id,
                details={"event_id": event.id, "risk_score": risk_score},
            )
        )

    db.add(
        AuditLog(
            action="event.ingested",
            entity_type=AuditEntityType.event,
            entity_id=event.id,
            details={"source": body.source, "risk_score": risk_score},
        )
    )
    await db.commit()
    await db.refresh(event)

    return EventResponse(
        id=event.id,
        source=event.source,
        author_hash=event.author_hash,
        raw_text=event.raw_text,
        clean_text=event.clean_text,
        url=event.url,
        risk_score=risk_score,
        severity=severity.value,
        incident_id=incident_id,
        created_at=event.created_at,
    )
