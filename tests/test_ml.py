import pytest

from app.ml.dataset import load_dataset
from app.ml.model import predict_fraud_proba, reset_model_cache
from app.ml.train import ensure_model_trained, train_model


@pytest.fixture(scope="module")
def model_metrics():
    reset_model_cache()
    return train_model()


def test_dataset_load():
    texts, labels = load_dataset()
    assert len(texts) >= 40
    assert len(labels) == len(texts)
    assert 0 in labels and 1 in labels


def test_train_metrics_meet_minimum(model_metrics):
    assert model_metrics["f1"] >= 0.68
    assert model_metrics["precision"] >= 0.70


def test_ensure_model_trained_cached():
    metrics = ensure_model_trained()
    assert metrics["f1"] >= 0.68


def test_predict_fraud_high():
    ensure_model_trained()
    score = predict_fraud_proba("срочно кредит займ без отказа перевод комиссия")
    assert score >= 0.5


def test_predict_fraud_low():
    ensure_model_trained()
    score = predict_fraud_proba("спасибо за консультацию по вкладу")
    assert score < 0.5
