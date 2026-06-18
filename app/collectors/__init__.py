"""Source collectors: dispatch by source_type."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors import rss, telegram_web
from app.models.source import MonitoredSource


async def collect_source(source: MonitoredSource, db: AsyncSession) -> int:
    """Run the right collector for a source. Returns number of new items ingested."""
    if source.source_type == "telegram":
        return await telegram_web.fetch_and_ingest(source, db)
    return await rss.fetch_and_ingest(source, db)
