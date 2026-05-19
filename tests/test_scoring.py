import pytest

from app.models.enums import Severity
from app.pipeline.scoring import compute_risk_score, risk_to_severity


def test_compute_risk_score_formula():
    score = compute_risk_score(
        rule_score=1.0,
        ml_score=0.0,
        graph_score=0.0,
        anomaly_score=0.0,
    )
    assert score == pytest.approx(0.35)


def test_compute_risk_score_all_ones():
    score = compute_risk_score(1.0, 1.0, 1.0, 1.0)
    assert score == pytest.approx(1.0)


def test_compute_risk_score_clamped():
    score = compute_risk_score(2.0, 2.0, 2.0, 2.0)
    assert score == pytest.approx(1.0)


def test_severity_low():
    assert risk_to_severity(0.1) == Severity.low


def test_severity_medium():
    assert risk_to_severity(0.5) == Severity.medium


def test_severity_high():
    assert risk_to_severity(0.85) == Severity.high


def test_severity_at_low_threshold():
    assert risk_to_severity(0.29) == Severity.low
    assert risk_to_severity(0.3) == Severity.medium


def test_severity_at_high_threshold():
    assert risk_to_severity(0.7) == Severity.high
    assert risk_to_severity(0.69) == Severity.medium
