"""Tests for the Telegram web-preview collector (t.me/s/, no auth)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.collectors.telegram_web import (
    _channel_handle,
    _parse_messages,
    _strip_html,
    fetch_and_ingest,
)
from app.models.event import Event
from app.models.seen_item import SeenItem
from app.models.source import MonitoredSource


# ── unit: handle normalization ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("@trendach", "trendach"),
        ("trendach", "trendach"),
        ("https://t.me/trendach", "trendach"),
        ("https://t.me/s/trendach", "trendach"),
        ("https://t.me/trendach/", "trendach"),
    ],
)
def test_channel_handle(raw, expected):
    assert _channel_handle(raw) == expected


# ── unit: html parsing ───────────────────────────────────────────────────────


def test_strip_html_unescapes_and_removes_tags():
    assert _strip_html('<b>Привет</b> &amp; <a href="x">мир</a>') == "Привет & мир"


def test_parse_messages_pairs_id_and_text():
    page = (
        '<div class="tgme_widget_message" data-post="chan/1">'
        '<div class="tgme_widget_message_text js-message_text">Первое сообщение</div></div>'
        '<div class="tgme_widget_message" data-post="chan/2">'
        '<div class="tgme_widget_message_text">Второе</div></div>'
    )
    msgs = _parse_messages(page)
    assert msgs == [("chan/1", "Первое сообщение"), ("chan/2", "Второе")]


def test_parse_messages_empty_page():
    assert _parse_messages("<html></html>") == []


# ── integration: fetch_and_ingest ────────────────────────────────────────────


def _src():
    s = MonitoredSource()
    s.id = 1
    s.name = "TG"
    s.url = "@chan"
    s.source_type = "telegram"
    return s


_FAKE_PAGE = (
    '<div class="tgme_widget_message" data-post="chan/100">'
    '<div class="tgme_widget_message_text">Мошенники похитили деньги с карты обманом</div></div>'
)


@pytest.mark.asyncio
async def test_fetch_and_ingest_creates_event(db_session):
    with patch(
        "app.collectors.telegram_web._fetch_page",
        new=AsyncMock(return_value=_FAKE_PAGE),
    ):
        count = await fetch_and_ingest(_src(), db_session)

    assert count == 1
    from sqlalchemy import select

    events = list((await db_session.execute(select(Event))).scalars().all())
    assert len(events) == 1
    assert events[0].url == "https://t.me/chan/100"
    assert events[0].source == "TG"


@pytest.mark.asyncio
async def test_fetch_and_ingest_skips_duplicate(db_session):
    with patch(
        "app.collectors.telegram_web._fetch_page",
        new=AsyncMock(return_value=_FAKE_PAGE),
    ):
        first = await fetch_and_ingest(_src(), db_session)
        second = await fetch_and_ingest(_src(), db_session)

    assert first == 1
    assert second == 0


@pytest.mark.asyncio
async def test_fetch_and_ingest_fetch_failure_returns_zero(db_session):
    with patch(
        "app.collectors.telegram_web._fetch_page", new=AsyncMock(return_value=None)
    ):
        count = await fetch_and_ingest(_src(), db_session)
    assert count == 0


@pytest.mark.asyncio
async def test_seen_item_persisted(db_session):
    with patch(
        "app.collectors.telegram_web._fetch_page",
        new=AsyncMock(return_value=_FAKE_PAGE),
    ):
        await fetch_and_ingest(_src(), db_session)

    from sqlalchemy import select

    seen = list((await db_session.execute(select(SeenItem))).scalars().all())
    assert len(seen) == 1


# ── dispatch: collect_source routes by source_type ───────────────────────────


@pytest.mark.asyncio
async def test_collect_source_routes_telegram_to_web(db_session):
    from app.collectors import collect_source

    src = _src()
    with (
        patch(
            "app.collectors.telegram_web.fetch_and_ingest",
            new=AsyncMock(return_value=7),
        ) as tg,
        patch(
            "app.collectors.rss.fetch_and_ingest", new=AsyncMock(return_value=0)
        ) as rss,
    ):
        result = await collect_source(src, db_session)

    assert result == 7
    tg.assert_called_once()
    rss.assert_not_called()
