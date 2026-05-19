from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.database import create_tables, engine
import app.models  # noqa: F401 — registers all models with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
