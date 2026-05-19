import pytest

from app.pipeline.detection import FRAUD_KEYWORDS, run_detection


def test_rules_no_keywords():
    result = run_detection("обычное сообщение без триггеров", {})
    assert result["rule_score"] == pytest.approx(0.0)
    assert result["rule_flags"] == []


def test_rules_single_keyword():
    result = run_detection("нужен срочно кредит", {})
    assert "срочно" in result["rule_flags"]
    assert result["rule_score"] > 0.0


def test_rules_multiple_keywords_capped():
    text = " ".join(FRAUD_KEYWORDS[:6])
    result = run_detection(text, {})
    assert len(result["rule_flags"]) >= 4
    assert result["rule_score"] <= 1.0


def test_ml_high_risk_fraud_text():
    features = {"has_url": False, "has_phone": False, "exclamation_count": 0, "uppercase_ratio": 0.0}
    result = run_detection(
        "срочно кредит займ без отказа перевод комиссия",
        features,
    )
    assert result["ml_score"] >= 0.5


def test_ml_low_risk_normal_text():
    features = {"has_url": False, "has_phone": False, "exclamation_count": 0, "uppercase_ratio": 0.0}
    result = run_detection(
        "спасибо за консультацию по вкладу всё понятно",
        features,
    )
    assert result["ml_score"] < 0.5


def test_anomaly_stub_spike():
    features = {"text_len": 500, "word_count": 80, "exclamation_count": 10}
    result = run_detection("текст", features)
    assert result["anomaly_score"] > 0.0


def test_detect_returns_required_keys():
    result = run_detection("кредит срочно", {"has_url": True})
    assert set(result.keys()) == {
        "rule_score",
        "ml_score",
        "anomaly_score",
        "rule_flags",
    }
