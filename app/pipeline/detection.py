from app.ml.model import load_model, predict_fraud_proba
from app.pipeline.preprocessing import preprocess_text

# High-precision fraud markers ONLY. Generic financial words (кредит, счёт,
# процент, перевод, налог...) and promo words (розыгрыш, приз, бесплатно) were
# REMOVED: they appear constantly in legitimate finance news and ads, which is
# exactly what was producing false positives. The ML model (trained on 21k real
# messages) is the primary signal; these rules only add interpretable evidence
# for terms that almost never occur outside scams.
FRAUD_KEYWORDS: tuple[str, ...] = (
    "мошенник",
    "обман",
    "развод",
    "разблокир",
    "взлом",
    "пирамид",
    "предоплат",
    "без вложени",
    "пассивный доход",
    "гарантированный доход",
)

_RULE_STEP = 0.2
_ML_CAP = 1.0


def _rule_detection(clean_text: str) -> tuple[float, list[str]]:
    flags = [kw for kw in FRAUD_KEYWORDS if kw in clean_text]
    return min(1.0, len(flags) * _RULE_STEP), flags


def _ml_stub(features: dict) -> float:
    score = 0.0
    if features.get("has_url"):
        score += 0.25
    if features.get("has_phone"):
        score += 0.25
    if features.get("has_email"):
        score += 0.15
    if features.get("exclamation_count", 0) >= 3:
        score += 0.2
    if features.get("uppercase_ratio", 0.0) >= 0.5:
        score += 0.15
    return min(_ML_CAP, score)


def _ml_score(clean_text: str, features: dict) -> float:
    if load_model() is not None:
        return min(_ML_CAP, predict_fraud_proba(clean_text))
    return _ml_stub(features)


def _anomaly_stub(features: dict) -> float:
    """Score genuinely suspicious text shape — NOT length.

    Long normal posts (news) are not anomalies. We flag patterns scams use:
    shouting (CAPS), exclamation spam, and contact-grab combos (url + phone)."""
    score = 0.0
    if features.get("uppercase_ratio", 0.0) >= 0.3:
        score += 0.4
    if features.get("exclamation_count", 0) >= 3:
        score += 0.3
    # Contact-grab: a phone number in a channel post is a classic scam vector
    # (normal news posts don't ask you to call a number)
    if features.get("has_phone"):
        score += 0.3
    if features.get("has_url"):
        score += 0.2
    return min(1.0, score)


def run_detection(clean_text: str, features: dict, raw_text: str | None = None) -> dict:
    text_for_ml = clean_text or preprocess_text(raw_text or "")
    rule_score, rule_flags = _rule_detection(text_for_ml)
    return {
        "rule_score": rule_score,
        "ml_score": _ml_score(text_for_ml, features),
        "anomaly_score": _anomaly_stub(features),
        "rule_flags": rule_flags,
    }
