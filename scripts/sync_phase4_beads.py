#!/usr/bin/env python3
"""Child beads for fraud_monitor-0v3."""
import subprocess
from pathlib import Path

ROOT = Path("/root/danik/fraud_monitor")
PARENT = "fraud_monitor-0v3"


def run(*args: str) -> str:
    r = subprocess.run(["bd", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    return r.stdout.strip()


CHILDREN = [
    (
        "4.1 Демо-данные",
        """scripts/seed_demo.py + data/demo_events.csv.
POST /events для 7 строк. Проверка инцидентов в UI.""",
    ),
    (
        "4.2 Покрытие тестами",
        """pytest --cov=app --cov-fail-under=70.
Текущий итог ~89%. 66 тестов.""",
    ),
    (
        "4.3 Сборка UI и static",
        """npm run build → frontend/dist.
main.py отдаёт SPA на :8888 вместе с API.""",
    ),
    (
        "4.4 README и Swagger",
        """README.md — быстрый старт.
/docs и /redoc на FastAPI.""",
    ),
]


def main() -> None:
    run(
        "update",
        PARENT,
        "-d",
        """Фаза 4: финальная доводка.

Чеклист:
- demo_events.csv через seed_demo.py
- покрытие app >= 70%
- frontend/dist + uvicorn 0.0.0.0:8888
- README, Swagger /docs

Запуск: bash scripts/start.sh""",
    )

    for title, desc in CHILDREN:
        bid = run("create", title, "--parent", PARENT, "-t", "task", "-p", "2", "-d", desc, "--silent")
        run("close", bid, "--reason", "выполнено")
        print(bid, title)

    run("close", PARENT, "--reason", "demo, coverage 89%, UI build, README, swagger")
    print("closed", PARENT)
    print(run("children", PARENT))


if __name__ == "__main__":
    main()
