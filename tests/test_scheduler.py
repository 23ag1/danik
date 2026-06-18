"""Tests for collector scheduler and sources CRUD coverage."""

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.source import MonitoredSource
from app.tasks.scheduler import _run_due_sources


# ── fixtures ────────────────────────────────────────────────────────────────


def _source(
    id=1,
    name="Feed",
    url="http://feed.com/rss",
    enabled=True,
    interval_sec=300,
    last_fetched_at=None,
):
    s = MonitoredSource()
    s.id = id
    s.name = name
    s.url = url
    s.enabled = enabled
    s.interval_sec = interval_sec
    s.last_fetched_at = last_fetched_at
    return s


# ── _run_due_sources: unit tests with mocked DB ─────────────────────────────


@pytest.mark.asyncio
async def test_run_due_sources_calls_ingest_for_new_source():
    src = _source(last_fetched_at=None)

    async def fake_session_factory():
        session = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [src]
        session.execute = AsyncMock(return_value=result)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        return session

    session_calls = []

    class FakeContextManager:
        def __init__(self):
            self.session = AsyncMock()
            self.session.execute = AsyncMock(side_effect=self._execute_side_effect)
            self.session.commit = AsyncMock()
            self._call_count = 0

        async def _execute_side_effect(self, *args, **kwargs):
            self._call_count += 1
            if self._call_count == 1:
                result = MagicMock()
                result.scalars.return_value.all.return_value = [src]
                return result
            return MagicMock()

        async def __aenter__(self):
            return self.session

        async def __aexit__(self, *args):
            return False

    fake_cm = FakeContextManager()

    with (
        patch("app.tasks.scheduler.AsyncSessionLocal", return_value=fake_cm),
        patch(
            "app.tasks.scheduler.collect_source", new_callable=AsyncMock
        ) as mock_ingest,
    ):
        await _run_due_sources()

    mock_ingest.assert_called_once()


@pytest.mark.asyncio
async def test_run_due_sources_skips_recently_fetched():
    recent = datetime.now(timezone.utc) - timedelta(seconds=10)
    src = _source(last_fetched_at=recent, interval_sec=300)

    class FakeContextManager:
        def __init__(self):
            self.session = AsyncMock()

        async def __aenter__(self):
            result = MagicMock()
            result.scalars.return_value.all.return_value = [src]
            self.session.execute = AsyncMock(return_value=result)
            return self.session

        async def __aexit__(self, *args):
            return False

    with (
        patch(
            "app.tasks.scheduler.AsyncSessionLocal", return_value=FakeContextManager()
        ),
        patch(
            "app.tasks.scheduler.collect_source", new_callable=AsyncMock
        ) as mock_ingest,
    ):
        await _run_due_sources()

    mock_ingest.assert_not_called()


@pytest.mark.asyncio
async def test_run_due_sources_fetches_overdue_source():
    old = datetime.now(timezone.utc) - timedelta(seconds=400)
    src = _source(last_fetched_at=old, interval_sec=300)

    call_count = 0

    class FakeContextManager:
        def __init__(self):
            self.session = AsyncMock()
            self.session.commit = AsyncMock()

        async def __aenter__(self):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.scalars.return_value.all.return_value = [src]
            self.session.execute = AsyncMock(return_value=result)
            return self.session

        async def __aexit__(self, *args):
            return False

    with (
        patch("app.tasks.scheduler.AsyncSessionLocal", FakeContextManager),
        patch(
            "app.tasks.scheduler.collect_source", new_callable=AsyncMock
        ) as mock_ingest,
    ):
        await _run_due_sources()

    mock_ingest.assert_called_once()


@pytest.mark.asyncio
async def test_run_due_sources_handles_ingest_error_gracefully():
    src = _source(last_fetched_at=None)

    class FakeContextManager:
        def __init__(self):
            self.session = AsyncMock()
            self.session.commit = AsyncMock()

        async def __aenter__(self):
            result = MagicMock()
            result.scalars.return_value.all.return_value = [src]
            self.session.execute = AsyncMock(return_value=result)
            return self.session

        async def __aexit__(self, *args):
            return False

    with (
        patch("app.tasks.scheduler.AsyncSessionLocal", FakeContextManager),
        patch(
            "app.tasks.scheduler.collect_source",
            new_callable=AsyncMock,
            side_effect=Exception("network error"),
        ),
    ):
        # should not raise — error is caught in collector_loop, but _run_due_sources itself
        # propagates; here we verify it surfaces so collector_loop can log it
        with pytest.raises(Exception, match="network error"):
            await _run_due_sources()


# ── sources CRUD: integration via async_client ──────────────────────────────


@pytest.mark.asyncio
async def test_list_sources_empty(async_client):
    r = await async_client.get("/sources")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_source_defaults(async_client):
    r = await async_client.post(
        "/sources",
        json={
            "name": "Коммерсантъ",
            "url": "https://www.kommersant.ru/RSS/section-finance.xml",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["interval_sec"] == 300
    assert data["enabled"] is True
    assert data["last_fetched_at"] is None


@pytest.mark.asyncio
async def test_create_source_custom_interval(async_client):
    r = await async_client.post(
        "/sources",
        json={
            "name": "РБК",
            "url": "https://rbc.ru/rss/news.rss",
            "interval_sec": 120,
            "enabled": False,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["interval_sec"] == 120
    assert data["enabled"] is False


@pytest.mark.asyncio
async def test_patch_source_interval(async_client):
    r = await async_client.post(
        "/sources",
        json={
            "name": "Test",
            "url": "https://example.com/feed.xml",
        },
    )
    sid = r.json()["id"]

    r = await async_client.patch(f"/sources/{sid}", json={"interval_sec": 900})
    assert r.status_code == 200
    assert r.json()["interval_sec"] == 900
    assert r.json()["enabled"] is True  # unchanged


@pytest.mark.asyncio
async def test_patch_source_toggle_off(async_client):
    r = await async_client.post(
        "/sources",
        json={
            "name": "Test2",
            "url": "https://example2.com/feed.xml",
        },
    )
    sid = r.json()["id"]

    r = await async_client.patch(f"/sources/{sid}", json={"enabled": False})
    assert r.status_code == 200
    assert r.json()["enabled"] is False


@pytest.mark.asyncio
async def test_delete_source_then_not_listed(async_client):
    r = await async_client.post(
        "/sources",
        json={
            "name": "ToDelete",
            "url": "https://todelete.com/feed.xml",
        },
    )
    sid = r.json()["id"]

    await async_client.delete(f"/sources/{sid}")

    r = await async_client.get("/sources")
    assert all(s["id"] != sid for s in r.json())


# ── sources router: direct function calls for async coverage ────────────────


@pytest.mark.asyncio
async def test_list_sources_direct(db_session):
    from app.routers.sources import list_sources

    result = await list_sources(db=db_session)
    assert result == []


@pytest.mark.asyncio
async def test_create_source_direct(db_session):
    from app.routers.sources import create_source
    from app.schemas.source import SourceCreate

    body = SourceCreate(
        name="Direct Feed", url="https://direct.com/rss.xml", interval_sec=600
    )
    result = await create_source(body=body, db=db_session)
    assert result.name == "Direct Feed"
    assert result.interval_sec == 600
    assert result.id is not None


@pytest.mark.asyncio
async def test_patch_source_direct(db_session):
    from app.routers.sources import create_source, patch_source
    from app.schemas.source import SourceCreate, SourcePatch

    body = SourceCreate(name="PatchFeed", url="https://patch.com/rss.xml")
    created = await create_source(body=body, db=db_session)

    patched = await patch_source(
        source_id=created.id,
        body=SourcePatch(enabled=False, interval_sec=120),
        db=db_session,
    )
    assert patched.enabled is False
    assert patched.interval_sec == 120


@pytest.mark.asyncio
async def test_patch_source_direct_404(db_session):
    from fastapi import HTTPException
    from app.routers.sources import patch_source
    from app.schemas.source import SourcePatch

    with pytest.raises(HTTPException) as exc_info:
        await patch_source(
            source_id=99999, body=SourcePatch(enabled=False), db=db_session
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_source_direct(db_session):
    from app.routers.sources import create_source, delete_source, list_sources
    from app.schemas.source import SourceCreate

    body = SourceCreate(name="DelFeed", url="https://del.com/rss.xml")
    created = await create_source(body=body, db=db_session)

    await delete_source(source_id=created.id, db=db_session)

    remaining = await list_sources(db=db_session)
    assert all(s.id != created.id for s in remaining)


@pytest.mark.asyncio
async def test_delete_source_direct_404(db_session):
    from fastapi import HTTPException
    from app.routers.sources import delete_source

    with pytest.raises(HTTPException) as exc_info:
        await delete_source(source_id=99999, db=db_session)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_trigger_fetch_direct(db_session):
    from types import SimpleNamespace
    from unittest.mock import patch
    from app.routers.sources import create_source, trigger_fetch
    from app.schemas.source import SourceCreate

    created = await create_source(
        body=SourceCreate(name="TrigFeed", url="https://trig.com/rss.xml"),
        db=db_session,
    )

    fake_entry = SimpleNamespace(
        title="Test", summary="body", link="http://t.com/1", id="http://t.com/1"
    )
    with (
        patch(
            "app.collectors.rss._fetch_feed_bytes",
            new=AsyncMock(return_value=b"<rss/>"),
        ),
        patch(
            "app.collectors.rss.feedparser.parse",
            return_value=SimpleNamespace(entries=[fake_entry]),
        ),
    ):
        result = await trigger_fetch(source_id=created.id, db=db_session)

    assert result["ingested"] == 1


@pytest.mark.asyncio
async def test_trigger_fetch_404(db_session):
    from fastapi import HTTPException
    from app.routers.sources import trigger_fetch

    with pytest.raises(HTTPException) as exc_info:
        await trigger_fetch(source_id=99999, db=db_session)
    assert exc_info.value.status_code == 404
