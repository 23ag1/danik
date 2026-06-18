"""Telegram public-channel collector via web preview (t.me/s/<channel>).

No Telethon, no API keys, no phone login — reads the public HTML preview that
Telegram exposes for any public channel. Runs through the same scheduler poll
as RSS, so new channels work immediately without restarting the server.
"""

import html as html_lib
import logging
import re

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.seen_item import SeenItem
from app.models.source import MonitoredSource
from app.services.pipeline_runner import process_event_text
from app.utils import build_incident, hash_author, hash_item

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FraudMonitor/1.0; +https://github.com/23ag1/danik)",
    "Accept-Encoding": "identity",
}

_POST_RE = re.compile(r'data-post="([^"]+)"')
_TEXT_RE = re.compile(
    r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.DOTALL
)


def _channel_handle(url: str) -> str:
    """Normalize a source url into a bare channel handle.
    '@trendach' / 'trendach' / 'https://t.me/trendach' -> 'trendach'."""
    h = url.strip().rstrip("/")
    h = h.replace("https://t.me/s/", "").replace("https://t.me/", "")
    h = h.replace("http://t.me/s/", "").replace("http://t.me/", "")
    return h.lstrip("@").split("/")[0]


def _strip_html(fragment: str) -> str:
    fragment = (
        fragment.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    )
    fragment = re.sub(r"<[^>]+>", "", fragment)
    return html_lib.unescape(fragment).strip()


def _parse_messages(page: str) -> list[tuple[str, str]]:
    """Return [(post_id, text), ...] in document order.

    Pairs each data-post anchor with the first message-text div that follows it
    (and precedes the next anchor)."""
    posts = [(m.start(), m.group(1)) for m in _POST_RE.finditer(page)]
    texts = [(m.start(), _strip_html(m.group(1))) for m in _TEXT_RE.finditer(page)]

    out: list[tuple[str, str]] = []
    for i, (pos, post_id) in enumerate(posts):
        next_pos = posts[i + 1][0] if i + 1 < len(posts) else len(page)
        text = next((t for tp, t in texts if pos < tp < next_pos), "")
        if text:
            out.append((post_id, text))
    return out


async def _fetch_page(handle: str) -> str | None:
    url = f"https://t.me/s/{handle}"
    try:
        async with httpx.AsyncClient(
            timeout=30.0, follow_redirects=True, headers=_HEADERS
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as exc:
        logger.error("Telegram web fetch error for %s: %s", url, exc)
        return None


async def fetch_and_ingest(source: MonitoredSource, db: AsyncSession) -> int:
    """Pull one public Telegram channel via web preview, dedup, run pipeline.
    Returns number of new items ingested. Same contract as rss.fetch_and_ingest."""
    handle = _channel_handle(source.url)
    if not handle:
        logger.error("Cannot parse channel handle from %s", source.url)
        return 0

    page = await _fetch_page(handle)
    if page is None:
        return 0

    messages = _parse_messages(page)
    if not messages:
        return 0

    all_hashes = [hash_item(source.url, post_id) for post_id, _ in messages]
    existing = set(
        await db.scalars(
            select(SeenItem.item_hash).where(SeenItem.item_hash.in_(all_hashes))
        )
    )

    ingested = 0
    for (post_id, text), h in zip(messages, all_hashes):
        if h in existing:
            continue

        result = process_event_text(text)
        event = Event(
            source=source.name,
            author_hash=hash_author(post_id),
            raw_text=text,
            clean_text=result["clean_text"],
            url=f"https://t.me/{post_id}",
            meta={"risk_score": result["risk_score"], "severity": result["severity"]},
        )
        db.add(event)
        await db.flush()

        if result["risk_score"] >= 0.3:
            title = f"[TG] {text[:120]}"
            db.add(build_incident(event.id, title, result))

        db.add(SeenItem(item_hash=h))
        existing.add(h)
        ingested += 1

    await db.commit()
    logger.info("telegram source=%s ingested=%d", source.name, ingested)
    return ingested
