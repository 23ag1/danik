from datetime import datetime
from pydantic import BaseModel, HttpUrl


class SourceCreate(BaseModel):
    name: str
    url: str
    source_type: str = "rss"  # "rss" | "telegram"
    interval_sec: int = 300
    enabled: bool = True


class SourcePatch(BaseModel):
    enabled: bool | None = None
    interval_sec: int | None = None
    name: str | None = None


class SourceRead(BaseModel):
    id: int
    name: str
    url: str
    source_type: str
    enabled: bool
    interval_sec: int
    last_fetched_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
