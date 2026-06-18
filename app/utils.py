import hashlib

from app.models.incident import Incident


def hash_author(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()


def hash_item(feed_url: str, uid: str) -> str:
    return hashlib.sha256(f"{feed_url}::{uid}".encode()).hexdigest()


def build_incident(event_id: int, title: str, pipeline_result: dict) -> Incident:
    det = pipeline_result["detection"]
    return Incident(
        event_id=event_id,
        title=title,
        risk_score=pipeline_result["risk_score"],
        severity=pipeline_result["severity"],
        rule_score=det.get("rule_score", 0.0),
        ml_score=det.get("ml_score", 0.0),
        graph_score=pipeline_result.get("graph_score", 0.0),
        anomaly_score=det.get("anomaly_score", 0.0),
        rule_flags=det.get("rule_flags", []),
    )
