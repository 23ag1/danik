import logging

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.seen_item import SeenItem
from app.models.source import MonitoredSource
from app.services.pipeline_runner import process_event_text
from app.utils import build_incident, hash_author, hash_item

logger = logging.getLogger(__name__)


def _entry_uid(entry: object) -> str:
    return getattr(entry, "id", None) or getattr(entry, "link", "") or ""


def _item_hash(feed_url: str, entry: object) -> str:
    return hash_item(feed_url, _entry_uid(entry))


def _build_raw_text(entry: object) -> str:
    title = getattr(entry, "title", "") or ""
    summary = getattr(entry, "summary", "") or ""
    return f"{title} {summary}".strip()


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FraudMonitor/1.0; +https://github.com/23ag1/danik)",
    # Some feeds (e.g. RBC) stall on compressed responses — request uncompressed
    "Accept-Encoding": "identity",
}


async def _fetch_feed_bytes(url: str, attempts: int = 2) -> bytes | None:
    """Fetch raw feed bytes via async httpx (timeout + redirects + browser UA).
    feedparser's built-in fetch is blocking and has no timeout — do not use it.
    Retries once: some feeds (RBC) intermittently time out on the first request."""
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=True, headers=_HEADERS
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.content
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "RSS fetch attempt %d/%d failed for %s: %s", attempt, attempts, url, exc
            )
    logger.error("RSS fetch error for %s: %s", url, last_exc)
    return None


async def fetch_and_ingest(source: MonitoredSource, db: AsyncSession) -> int:
    """Pull one RSS feed, skip duplicates, run pipeline, persist events/incidents.
    Returns number of new items ingested."""
    content = await _fetch_feed_bytes(source.url)
    if content is None:
        return 0

    parsed = feedparser.parse(content)
    entries = parsed.entries
    if not entries:
        return 0

    # Batch dedup check — one query instead of N
    all_hashes = [_item_hash(source.url, e) for e in entries]
    existing_hashes = set(
        await db.scalars(
            select(SeenItem.item_hash).where(SeenItem.item_hash.in_(all_hashes))
        )
    )

    ingested = 0
    for entry, h in zip(entries, all_hashes):
        if h in existing_hashes:
            continue

        raw_text = _build_raw_text(entry)
        if not raw_text:
            continue

        result = process_event_text(raw_text)

        event = Event(
            source=source.name,
            author_hash=hash_author(_entry_uid(entry)),
            raw_text=raw_text,
            clean_text=result["clean_text"],
            url=getattr(entry, "link", None),
            meta={"risk_score": result["risk_score"], "severity": result["severity"]},
        )
        db.add(event)
        await db.flush()  # get event.id

        if result["risk_score"] >= 0.3:
            title = f"[RSS] {(getattr(entry, 'title', '') or raw_text)[:120]}"
            db.add(build_incident(event.id, title, result))

        db.add(SeenItem(item_hash=h))
        existing_hashes.add(h)  # guard against duplicate entries in same feed
        ingested += 1

    await db.commit()
    logger.info("source=%s ingested=%d", source.name, ingested)
    return ingested
