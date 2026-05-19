from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.config import settings

_MODEL: Pipeline | None = None


def model_paths() -> tuple[Path, Path]:
    base = Path(settings.ml_artifacts_dir)
    return base / "fraud_pipeline.joblib", base / "fraud_metrics.joblib"


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=5000)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def save_model(pipeline: Pipeline, metrics: dict[str, float]) -> None:
    model_path, metrics_path = model_paths()
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    joblib.dump(metrics, metrics_path)


def load_model() -> Pipeline | None:
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    model_path, _ = model_paths()
    if not model_path.exists():
        return None
    _MODEL = joblib.load(model_path)
    return _MODEL


def predict_fraud_proba(text: str) -> float:
    pipeline = load_model()
    if pipeline is None:
        return 0.0
    proba = pipeline.predict_proba([text])[0]
    classes = list(pipeline.named_steps["clf"].classes_)
    fraud_idx = classes.index(1) if 1 in classes else -1
    return float(proba[fraud_idx])


def reset_model_cache() -> None:
    global _MODEL
    _MODEL = None
