from datetime import datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    source: str = Field(..., max_length=100)
    user_id: str = Field(..., min_length=1)
    raw_text: str = ""
    url: str | None = Field(None, max_length=512)
    meta: dict = Field(default_factory=dict)


class EventResponse(BaseModel):
    id: int
    source: str
    author_hash: str
    raw_text: str
    clean_text: str
    url: str | None
    risk_score: float
    severity: str
    incident_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventRead(BaseModel):
    id: int
    source: str
    author_hash: str
    raw_text: str
    url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
