import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.event import Event
from app.models.incident import Incident
from app.models.audit import AuditLog
from app.models.enums import Severity, IncidentStatus

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()


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
    await db_session.commit()
    await db_session.refresh(event)

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
        entity_type="incident",
        entity_id=42,
        actor="analyst_hash_001",
        details={"old_status": "new", "new_status": "confirmed"},
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.id is not None
    assert log.action == "incident.confirmed"
    assert log.entity_type == "incident"
    assert log.details["old_status"] == "new"
    assert log.created_at is not None


async def test_audit_log_default_actor(db_session: AsyncSession):
    log = AuditLog(action="event.ingested", entity_type="event", entity_id=1)
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.actor == "system"
    assert log.details == {}
