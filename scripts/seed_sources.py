"""Seed default Russian financial RSS sources for demo."""

import asyncio
import sys
from pathlib import Path

# Force UTF-8 console output (Windows consoles default to cp866/cp1251)
sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.database import AsyncSessionLocal, create_tables
from app.models.source import MonitoredSource

SOURCES = [
    {
        "name": "Коммерсантъ Финансы",
        "url": "https://www.kommersant.ru/RSS/section-finance.xml",
        "interval_sec": 300,
    },
    {
        "name": "РБК Финансы",
        "url": "https://rssexport.rbc.ru/rbcnews/news/30/full.rss",
        "interval_sec": 300,
    },
    {
        "name": "Банки.ру Новости",
        "url": "https://www.banki.ru/xml/news.rss",
        "interval_sec": 600,
    },
    {
        "name": "ЦБ РФ Пресс-релизы",
        "url": "https://www.cbr.ru/rss/RssPress",
        "interval_sec": 3600,
    },
]


async def main() -> None:
    await create_tables()
    async with AsyncSessionLocal() as db:
        existing = set(await db.scalars(select(MonitoredSource.url)))
        added = 0
        for s in SOURCES:
            if s["url"] in existing:
                print(f"  skip (exists): {s['name']}")
                continue
            db.add(MonitoredSource(**s))
            added += 1
        await db.commit()
    print(f"Seeded {added} sources ({len(SOURCES) - added} skipped).")


asyncio.run(main())
