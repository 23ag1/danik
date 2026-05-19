from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.incident import Incident
from app.models.audit import AuditLog
from app.models.enums import Severity, IncidentStatus, AuditEntityType


async def test_create_event(db_session: AsyncSession):
    event = Event(source="telegram", author_hash="abc123hash", raw_text="buy crypto now!")
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    assert event.id is not None
    assert event.source == "telegram"
    assert event.author_hash == "abc123hash"
    assert event.clean_text == ""
    assert event.created_at is not None


async def test_create_incident(db_session: AsyncSession):
    event = Event(source="vk", author_hash="xyz789hash")
    db_session.add(event)
    await db_session.flush()  # assigns event.id without committing

    incident = Incident(
        event_id=event.id,
        title="Подозрительная активность",
        risk_score=0.85,
        severity=Severity.high,
        ml_score=0.9,
        rule_score=0.8,
        rule_flags=["кредит", "срочно"],
    )
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)

    assert incident.id is not None
    assert incident.severity == Severity.high
    assert incident.status == IncidentStatus.new
    assert incident.rule_flags == ["кредит", "срочно"]
    assert incident.analyst_comment is None


async def test_create_audit_log(db_session: AsyncSession):
    log = AuditLog(
        action="incident.confirmed",
        entity_type=AuditEntityType.incident,
        entity_id=42,
        actor="analyst_hash_001",
        details={"old_status": "new", "new_status": "confirmed"},
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.id is not None
    assert log.action == "incident.confirmed"
    assert log.entity_type == AuditEntityType.incident
    assert log.details["old_status"] == "new"
    assert log.created_at is not None


async def test_audit_log_default_actor(db_session: AsyncSession):
    log = AuditLog(action="event.ingested", entity_type=AuditEntityType.event, entity_id=1)
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.actor == "system"
    assert log.details == {}
