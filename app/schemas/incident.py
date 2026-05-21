from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import IncidentStatus, Severity


class IncidentRead(BaseModel):
    id: int
    event_id: int
    title: str
    raw_text: str
    risk_score: float
    severity: Severity
    rule_score: float
    ml_score: float
    graph_score: float
    anomaly_score: float
    rule_flags: list
    status: IncidentStatus
    analyst_comment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus
    analyst_comment: str | None = None
