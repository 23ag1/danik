from app.pipeline.detection import run_detection
from app.pipeline.features import extract_features
from app.pipeline.preprocessing import preprocess_text
from app.pipeline.scoring import compute_risk_score, risk_to_severity


def process_event_text(raw_text: str, graph_score: float = 0.0) -> dict:
    clean_text = preprocess_text(raw_text)
    features = extract_features(raw_text)
    detection = run_detection(clean_text, features, raw_text=raw_text)
    risk_score = compute_risk_score(
        rule_score=detection["rule_score"],
        ml_score=detection["ml_score"],
        graph_score=graph_score,
        anomaly_score=detection["anomaly_score"],
    )
    return {
        "clean_text": clean_text,
        "features": features,
        "detection": detection,
        "graph_score": graph_score,
        "risk_score": risk_score,
        "severity": risk_to_severity(risk_score),
    }
