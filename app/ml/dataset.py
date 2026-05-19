from pathlib import Path

import pandas as pd

DEFAULT_DATASET = Path(__file__).resolve().parents[2] / "data" / "fraud_train.csv"


def load_dataset(path: Path | None = None) -> tuple[list[str], list[int]]:
    csv_path = path or DEFAULT_DATASET
    frame = pd.read_csv(csv_path)
    texts = frame["text"].astype(str).tolist()
    labels = frame["label"].astype(int).tolist()
    return texts, labels
