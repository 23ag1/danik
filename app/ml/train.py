from pathlib import Path

from sklearn.model_selection import train_test_split

from app.ml.dataset import load_dataset
from app.ml.metrics import classification_metrics
from app.ml.model import build_pipeline, model_paths, reset_model_cache, save_model


def train_model(dataset_path: Path | None = None) -> dict[str, float]:
    texts, labels = load_dataset(dataset_path)
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test).tolist()
    metrics = classification_metrics(y_test, y_pred)

    reset_model_cache()
    save_model(pipeline, metrics)
    return metrics


def ensure_model_trained(dataset_path: Path | None = None) -> dict[str, float]:
    model_path, metrics_path = model_paths()
    if model_path.exists() and metrics_path.exists():
        import joblib

        return joblib.load(metrics_path)
    return train_model(dataset_path)


if __name__ == "__main__":
    # `python -m app.ml.train` always retrains from the current dataset.
    metrics = train_model()
    print("Model trained:", {k: round(v, 3) for k, v in metrics.items()})
