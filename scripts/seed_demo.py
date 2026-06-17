#!/usr/bin/env python3
"""Загрузить demo_events.csv через POST /events."""

import csv
import sys
from pathlib import Path

import httpx

# Force UTF-8 console output (Windows consoles default to cp866/cp1251)
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "demo_events.csv"
API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8888"


def main() -> None:
    if not CSV_PATH.exists():
        print(f"нет файла {CSV_PATH}")
        sys.exit(1)

    ok = 0
    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with httpx.Client(base_url=API, timeout=30) as client:
        for row in rows:
            payload = {
                "source": row["source"].strip(),
                "user_id": row["user_id"].strip(),
                "raw_text": row["raw_text"].strip(),
                "url": row.get("url", "").strip() or None,
            }
            r = client.post("/events", json=payload)
            r.raise_for_status()
            data = r.json()
            ok += 1
            print(
                f"#{data['id']} risk={data['risk_score']:.2f} incident={data.get('incident_id')}"
            )

    print(f"готово: {ok} событий")


if __name__ == "__main__":
    main()
