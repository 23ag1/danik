from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.rss import fetch_and_ingest
from app.database import get_db
from app.models.source import MonitoredSource
from app.schemas.source import SourceCreate, SourcePatch, SourceRead

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonitoredSource).order_by(MonitoredSource.id))
    return list(result.scalars().all())


@router.post("", response_model=SourceRead, status_code=201)
async def create_source(body: SourceCreate, db: AsyncSession = Depends(get_db)):
    source = MonitoredSource(
        name=body.name,
        url=str(body.url),
        interval_sec=body.interval_sec,
        enabled=body.enabled,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.patch("/{source_id}", response_model=SourceRead)
async def patch_source(
    source_id: int, body: SourcePatch, db: AsyncSession = Depends(get_db)
):
    source = await db.get(MonitoredSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if body.enabled is not None:
        source.enabled = body.enabled
    if body.interval_sec is not None:
        source.interval_sec = body.interval_sec
    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await db.get(MonitoredSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
    await db.commit()


@router.post("/{source_id}/fetch", response_model=dict)
async def trigger_fetch(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await db.get(MonitoredSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    ingested = await fetch_and_ingest(source, db)
    return {"ingested": ingested}
