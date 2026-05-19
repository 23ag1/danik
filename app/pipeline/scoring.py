from app.config import settings
from app.models.enums import Severity


def compute_risk_score(
    rule_score: float,
    ml_score: float,
    graph_score: float = 0.0,
    anomaly_score: float = 0.0,
) -> float:
    total = (
        settings.risk_weight_rule * rule_score
        + settings.risk_weight_ml * ml_score
        + settings.risk_weight_graph * graph_score
        + settings.risk_weight_anomaly * anomaly_score
    )
    return min(1.0, max(0.0, total))


def risk_to_severity(risk_score: float) -> Severity:
    if risk_score >= settings.risk_threshold_high:
        return Severity.high
    if risk_score >= settings.risk_threshold_low:
        return Severity.medium
    return Severity.low
