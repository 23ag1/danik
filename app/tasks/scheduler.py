import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.collectors import collect_source
from app.database import AsyncSessionLocal
from app.models.source import MonitoredSource

logger = logging.getLogger(__name__)

_CHECK_INTERVAL = 60  # seconds between scheduler ticks


async def collector_loop() -> None:
    """Background task: poll all due sources (RSS + Telegram web preview).

    Telegram channels are collected via t.me/s/ web preview through the same
    poll loop, so newly added channels are picked up on the next tick without
    any restart or Telegram login."""
    logger.info("collector_loop started")
    while True:
        try:
            await _run_due_sources()
        except Exception as exc:
            logger.error("collector_loop tick error: %s", exc)
        await asyncio.sleep(_CHECK_INTERVAL)


async def stop_collectors() -> None:
    """Kept for lifespan shutdown compatibility — no background listener anymore."""
    return None


async def _run_due_sources() -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MonitoredSource).where(MonitoredSource.enabled.is_(True))
        )
        sources = list(result.scalars().all())

    for source in sources:
        last = source.last_fetched_at
        # SQLite returns naive datetimes — assume UTC to compare with offset-aware now
        if last is not None and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last is not None and (now - last).total_seconds() < source.interval_sec:
            continue

        async with AsyncSessionLocal() as db:
            await collect_source(source, db)
            await db.execute(
                update(MonitoredSource)
                .where(MonitoredSource.id == source.id)
                .values(last_fetched_at=datetime.now(timezone.utc))
            )
            await db.commit()
