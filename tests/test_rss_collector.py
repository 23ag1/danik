"""Tests for RSS collector and sources API."""

import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.collectors.rss import _build_raw_text, _entry_uid, _item_hash, fetch_and_ingest
from app.utils import hash_author
from app.models.source import MonitoredSource
from app.models.seen_item import SeenItem
from app.models.event import Event
from app.models.incident import Incident


# ── helpers ─────────────────────────────────────────────────────────────────


def _make_entry(
    title="Fraud alert",
    summary="Someone did something bad",
    link="http://x.com/1",
    entry_id="http://x.com/1",
):
    return SimpleNamespace(title=title, summary=summary, link=link, id=entry_id)


def _make_source(url="http://feed.example.com/rss", name="TestFeed"):
    src = MonitoredSource()
    src.id = 1
    src.name = name
    src.url = url
    src.enabled = True
    src.interval_sec = 300
    src.last_fetched_at = None
    return src


def _fake_parsed(entries):
    return SimpleNamespace(entries=entries)


def _patch_feed(entries):
    """Patch both the async byte-fetch and feedparser.parse for a fake feed."""
    return (
        patch(
            "app.collectors.rss._fetch_feed_bytes",
            new=AsyncMock(return_value=b"<rss/>"),
        ),
        patch(
            "app.collectors.rss.feedparser.parse", return_value=_fake_parsed(entries)
        ),
    )


# ── unit tests: pure functions ───────────────────────────────────────────────


def test_item_hash_deterministic():
    entry = _make_entry()
    h1 = _item_hash("http://feed.com/rss", entry)
    h2 = _item_hash("http://feed.com/rss", entry)
    assert h1 == h2
    assert len(h1) == 64


def test_item_hash_different_feeds():
    entry = _make_entry()
    h1 = _item_hash("http://feed1.com/rss", entry)
    h2 = _item_hash("http://feed2.com/rss", entry)
    assert h1 != h2


def test_build_raw_text_combines():
    entry = _make_entry(title="Hello", summary="World")
    assert _build_raw_text(entry) == "Hello World"


def test_build_raw_text_missing_summary():
    entry = SimpleNamespace(title="Only title")
    assert _build_raw_text(entry) == "Only title"


def test_author_hash_is_sha256_of_id():
    entry = _make_entry(entry_id="http://x.com/1")
    expected = hashlib.sha256("http://x.com/1".encode()).hexdigest()
    assert hash_author(_entry_uid(entry)) == expected


# ── integration tests: fetch_and_ingest ─────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_and_ingest_creates_event(db_session):
    source = _make_source()
    entry = _make_entry(
        title="Мошенничество", summary="Детали мошеннической схемы с кредитами"
    )

    p_bytes, p_parse = _patch_feed([entry])
    with p_bytes, p_parse:
        count = await fetch_and_ingest(source, db_session)

    assert count == 1

    from sqlalchemy import select

    events = list((await db_session.execute(select(Event))).scalars().all())
    assert len(events) == 1
    assert "Мошенничество" in events[0].raw_text
    assert events[0].source == "TestFeed"


@pytest.mark.asyncio
async def test_fetch_and_ingest_skips_duplicate(db_session):
    source = _make_source()
    entry = _make_entry()

    p_bytes, p_parse = _patch_feed([entry])
    with p_bytes, p_parse:
        first = await fetch_and_ingest(source, db_session)
        second = await fetch_and_ingest(source, db_session)

    assert first == 1
    assert second == 0  # duplicate skipped


@pytest.mark.asyncio
async def test_fetch_and_ingest_seen_item_persisted(db_session):
    source = _make_source()
    entry = _make_entry()

    p_bytes, p_parse = _patch_feed([entry])
    with p_bytes, p_parse:
        await fetch_and_ingest(source, db_session)

    from sqlalchemy import select

    seen = list((await db_session.execute(select(SeenItem))).scalars().all())
    assert len(seen) == 1


@pytest.mark.asyncio
async def test_fetch_and_ingest_fetch_failure_returns_zero(db_session):
    """Network/fetch failure -> _fetch_feed_bytes returns None -> ingest 0."""
    source = _make_source()

    with patch(
        "app.collectors.rss._fetch_feed_bytes", new=AsyncMock(return_value=None)
    ):
        count = await fetch_and_ingest(source, db_session)

    assert count == 0


@pytest.mark.asyncio
async def test_fetch_and_ingest_empty_text_skipped(db_session):
    source = _make_source()
    entry = SimpleNamespace(title="", link="http://x.com/2", id="http://x.com/2")

    p_bytes, p_parse = _patch_feed([entry])
    with p_bytes, p_parse:
        count = await fetch_and_ingest(source, db_session)

    assert count == 0


# ── API tests: /sources ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sources_crud(async_client):
    # create
    r = await async_client.post(
        "/sources",
        json={
            "name": "Test Feed",
            "url": "http://example.com/rss.xml",
            "interval_sec": 600,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Feed"
    assert data["enabled"] is True
    source_id = data["id"]

    # list
    r = await async_client.get("/sources")
    assert r.status_code == 200
    assert any(s["id"] == source_id for s in r.json())

    # patch
    r = await async_client.patch(f"/sources/{source_id}", json={"enabled": False})
    assert r.status_code == 200
    assert r.json()["enabled"] is False

    # delete
    r = await async_client.delete(f"/sources/{source_id}")
    assert r.status_code == 204

    r = await async_client.get("/sources")
    assert all(s["id"] != source_id for s in r.json())


@pytest.mark.asyncio
async def test_sources_patch_404(async_client):
    r = await async_client.patch("/sources/99999", json={"enabled": False})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_sources_delete_404(async_client):
    r = await async_client.delete("/sources/99999")
    assert r.status_code == 404
