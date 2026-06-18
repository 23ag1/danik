"""Telegram channel listener — adapted from polymarket-bot/src/telegram/listener.py.

Connects as a user account (Telethon), monitors channels stored in MonitoredSource
(source_type='telegram'), runs each message through process_event_text(), deduplicates
via SeenItem, saves Event + Incident to DB.

Requires: TG_API_ID, TG_API_HASH in .env. Run scripts/auth_tg.py once to create session.
TG sources are resolved once at startup; add new channels via /sources then restart.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityTextUrl

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.event import Event
from app.models.seen_item import SeenItem
from app.models.source import MonitoredSource
from app.services.pipeline_runner import process_event_text
from app.utils import build_incident, hash_author, hash_item

logger = logging.getLogger(__name__)


def _tg_item_hash(channel_id: int, message_id: int) -> str:
    return hash_item(f"tg:{channel_id}", str(message_id))


def _extract_urls(message) -> list[str]:
    if not message.entities:
        return []
    return [
        e.url for e in message.entities if isinstance(e, MessageEntityTextUrl) and e.url
    ]


async def _ingest_message(
    db: AsyncSession, channel_id: int, channel_name: str, message
) -> bool:
    """Process one TG message. Returns True if new, False if duplicate or empty."""
    h = _tg_item_hash(channel_id, message.id)

    if await db.scalar(select(SeenItem.id).where(SeenItem.item_hash == h)):
        return False

    raw_text = message.raw_text or ""
    if not raw_text.strip():
        return False

    result = process_event_text(raw_text)
    author = hash_author(str(getattr(message, "sender_id", channel_id) or channel_id))
    urls = _extract_urls(message)

    event = Event(
        source=channel_name,
        author_hash=author,
        raw_text=raw_text,
        clean_text=result["clean_text"],
        url=urls[0] if urls else None,
        meta={
            "tg_message_id": message.id,
            "tg_channel_id": channel_id,
            "risk_score": result["risk_score"],
            "severity": result["severity"],
        },
    )
    db.add(event)
    await db.flush()

    if result["risk_score"] >= 0.3:
        db.add(build_incident(event.id, f"[TG] {raw_text[:120]}", result))

    db.add(SeenItem(item_hash=h))
    await db.commit()
    return True


async def _load_telegram_sources() -> list[MonitoredSource]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MonitoredSource).where(
                MonitoredSource.source_type == "telegram",
                MonitoredSource.enabled.is_(True),
            )
        )
        return list(result.scalars().all())


def create_client() -> TelegramClient:
    return TelegramClient(
        settings.tg_session_name, settings.tg_api_id, settings.tg_api_hash
    )


async def start_telegram_collector() -> None:
    """Start Telethon client and listen for messages from all configured TG sources.
    Returns immediately if TG credentials not configured or no telegram sources exist.
    """
    if not settings.tg_api_id or not settings.tg_api_hash:
        logger.info("TG_API_ID/TG_API_HASH not set — Telegram collector disabled")
        return

    sources = await _load_telegram_sources()
    if not sources:
        logger.info("No enabled telegram sources in DB — Telegram collector disabled")
        return

    client = create_client()
    # channel_map is write-once after _resolve_sources() completes, then read-only
    channel_map: dict[int, str] = {}

    async def _resolve_sources() -> list[int]:
        ids = []
        for src in sources:
            try:
                entity = await client.get_entity(src.url)
                channel_map[entity.id] = src.name
                ids.append(entity.id)
                logger.info("Resolved '%s' (%s) -> id=%d", src.name, src.url, entity.id)
            except Exception as exc:
                logger.error("Cannot resolve '%s' (%s): %s", src.name, src.url, exc)
        return ids

    await client.connect()
    if not await client.is_user_authorized():
        logger.error(
            "Telegram session not authorized — run `python scripts/auth_tg.py` "
            "to log in. Telegram collector disabled."
        )
        await client.disconnect()
        return
    logger.info("Telegram client connected")

    channel_ids = await _resolve_sources()
    if not channel_ids:
        logger.error("No TG sources resolved — stopping TG collector")
        await client.disconnect()
        return

    # Backfill: one session for all channels, break on first duplicate per channel
    async with AsyncSessionLocal() as db:
        for cid in channel_ids:
            try:
                async for msg in client.iter_messages(cid, limit=50):
                    if not await _ingest_message(
                        db, cid, channel_map.get(cid, str(cid)), msg
                    ):
                        break
            except Exception as exc:
                logger.error("Backfill error for channel %d: %s", cid, exc)

    @client.on(events.NewMessage(chats=channel_ids))
    async def _on_message(event: events.NewMessage.Event) -> None:
        cid = event.chat_id
        name = channel_map.get(cid, str(cid))
        async with AsyncSessionLocal() as db:
            new = await _ingest_message(db, cid, name, event.message)
        if new:
            logger.info("TG new message: channel=%s msg_id=%d", name, event.id)

    logger.info("Telegram listener active for %d channel(s)", len(channel_ids))
    await client.run_until_disconnected()
