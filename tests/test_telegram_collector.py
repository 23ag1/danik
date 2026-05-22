"""Tests for Telegram collector."""
import pytest
from unittest.mock import MagicMock

from app.collectors.telegram import _tg_item_hash, _extract_urls, _ingest_message


def _make_message(msg_id=1, text="Мошенничество с кредитами", sender_id=12345, entities=None):
    msg = MagicMock()
    msg.id = msg_id
    msg.raw_text = text
    msg.sender_id = sender_id
    msg.entities = entities or []
    return msg


# ── unit tests ───────────────────────────────────────────────────────────────


def test_tg_item_hash_deterministic():
    h1 = _tg_item_hash(111, 42)
    h2 = _tg_item_hash(111, 42)
    assert h1 == h2
    assert len(h1) == 64


def test_tg_item_hash_different_channels():
    assert _tg_item_hash(111, 42) != _tg_item_hash(222, 42)


def test_tg_item_hash_different_messages():
    assert _tg_item_hash(111, 1) != _tg_item_hash(111, 2)


def test_extract_urls_empty():
    msg = _make_message(entities=[])
    assert _extract_urls(msg) == []


def test_extract_urls_finds_text_url():
    from telethon.tl.types import MessageEntityTextUrl
    entity = MagicMock(spec=MessageEntityTextUrl)
    entity.url = "https://example.com"
    msg = _make_message(entities=[entity])
    assert _extract_urls(msg) == ["https://example.com"]


# ── integration: _ingest_message (db passed directly) ────────────────────────


@pytest.mark.asyncio
async def test_ingest_message_creates_event(db_session):
    from sqlalchemy import select
    from app.models.event import Event

    msg = _make_message(text="Мошеннический кредит с накруткой процентов")
    result = await _ingest_message(db_session, 111, "TestChannel", msg)

    assert result is True
    events = list((await db_session.execute(select(Event))).scalars().all())
    assert len(events) == 1
    assert events[0].source == "TestChannel"


@pytest.mark.asyncio
async def test_ingest_message_skips_duplicate(db_session):
    msg = _make_message(msg_id=99, text="Дублирующееся сообщение о фроде")

    first = await _ingest_message(db_session, 111, "Chan", msg)
    second = await _ingest_message(db_session, 111, "Chan", msg)

    assert first is True
    assert second is False


@pytest.mark.asyncio
async def test_ingest_message_skips_empty_text(db_session):
    msg = _make_message(text="")
    result = await _ingest_message(db_session, 111, "Chan", msg)
    assert result is False


# ── API: source_type field ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_telegram_source(async_client):
    r = await async_client.post("/sources", json={
        "name": "Test TG Channel",
        "url": "@test_channel",
        "source_type": "telegram",
    })
    assert r.status_code == 201
    assert r.json()["source_type"] == "telegram"


@pytest.mark.asyncio
async def test_create_rss_source_default_type(async_client):
    r = await async_client.post("/sources", json={
        "name": "RSS Feed",
        "url": "https://example.com/rss.xml",
    })
    assert r.status_code == 201
    assert r.json()["source_type"] == "rss"


@pytest.mark.asyncio
async def test_create_source_invalid_type(async_client):
    r = await async_client.post("/sources", json={
        "name": "Bad",
        "url": "https://bad.com/rss.xml",
        "source_type": "vk",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_patch_source_name(async_client):
    r = await async_client.post("/sources", json={"name": "Old", "url": "https://old.com/rss.xml"})
    sid = r.json()["id"]
    r = await async_client.patch(f"/sources/{sid}", json={"name": "New"})
    assert r.status_code == 200
    assert r.json()["name"] == "New"
