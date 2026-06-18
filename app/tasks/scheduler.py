import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.collectors.rss import fetch_and_ingest
from app.database import AsyncSessionLocal
from app.models.source import MonitoredSource

logger = logging.getLogger(__name__)

_CHECK_INTERVAL = 60  # seconds between scheduler ticks
_tg_task: asyncio.Task | None = None


async def collector_loop() -> None:
    """Background task: RSS polling + optional Telegram listener."""
    global _tg_task
    logger.info("collector_loop started")
    from app.collectors.telegram import start_telegram_collector

    _tg_task = asyncio.create_task(start_telegram_collector())
    while True:
        await asyncio.sleep(_CHECK_INTERVAL)
        try:
            await _run_due_sources()
        except Exception as exc:
            logger.error("collector_loop tick error: %s", exc)


async def stop_collectors() -> None:
    """Cancel the Telegram listener task. Called from lifespan shutdown."""
    global _tg_task
    if _tg_task and not _tg_task.done():
        _tg_task.cancel()
        await asyncio.gather(_tg_task, return_exceptions=True)
    _tg_task = None


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
            await fetch_and_ingest(source, db)
            await db.execute(
                update(MonitoredSource)
                .where(MonitoredSource.id == source.id)
                .values(last_fetched_at=datetime.now(timezone.utc))
            )
            await db.commit()
