import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.collectors.rss import fetch_and_ingest
from app.database import AsyncSessionLocal
from app.models.source import MonitoredSource

logger = logging.getLogger(__name__)

_CHECK_INTERVAL = 60  # seconds between scheduler ticks


async def collector_loop() -> None:
    """Background task: every _CHECK_INTERVAL seconds, poll all due RSS sources."""
    logger.info("collector_loop started")
    while True:
        await asyncio.sleep(_CHECK_INTERVAL)
        try:
            await _run_due_sources()
        except Exception as exc:
            logger.error("collector_loop tick error: %s", exc)


async def _run_due_sources() -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MonitoredSource).where(MonitoredSource.enabled.is_(True))
        )
        sources = list(result.scalars().all())

    for source in sources:
        last = source.last_fetched_at
        if last is not None and (now - last).total_seconds() < source.interval_sec:
            continue

        async with AsyncSessionLocal() as db:
            await fetch_and_ingest(source, db)
            await db.execute(
                update(MonitoredSource)
                .where(MonitoredSource.id == source.id)
                .values(last_fetched_at=datetime.now(timezone.utc))
            )
            await db.commit()
