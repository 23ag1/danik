#!/usr/bin/env python3
"""Sync phase 3 child beads under fraud_monitor-6q0."""
import subprocess
from pathlib import Path

ROOT = Path("/root/danik/fraud_monitor")
PARENT = "fraud_monitor-6q0"


def run(*args: str) -> str:
    result = subprocess.run(
        ["bd", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


UPDATES = [
    (
        "fraud_monitor-6q0.1",
        "3.1 План и docs",
        """docs/frontend-architecture.md — слои и команды запуска.

Решения: FSD-lite (app, shared, pages). Без TanStack Query, widgets, Framer.""",
    ),
    (
        "fraud_monitor-6q0.2",
        "3.2 Scaffold frontend",
        """frontend/: Vite, React 18, TypeScript, Tailwind v4, React Router.

vite.config.ts — proxy /api на порт 8000.
Команды: npm install, npm run dev, npm run build.""",
    ),
    (
        "fraud_monitor-6q0.3",
        "3.3 shared: api, types, ui",
        """shared/types.ts — Incident, EventCreate, Severity, IncidentStatus.

shared/api.ts — getIncidents, patchIncident, createEvent. BASE=/api.

shared/ui/Layout.tsx — навигация.
shared/ui/Badge.tsx — severity и status.""",
    ),
]

CREATES = [
    (
        "3.4 DashboardPage",
        """pages/DashboardPage.tsx

GET /incidents: KPI всего, новых, high, средний risk.
Список последних 8 со ссылками.
Пусто — ссылка на /ingest.""",
    ),
    (
        "3.5 IncidentsPage",
        """pages/IncidentsPage.tsx

Таблица: id, title, risk, severity, status.
Фильтры на клиенте: status, severity, поиск по title.""",
    ),
    (
        "3.6 IncidentDetailPage",
        """pages/IncidentDetailPage.tsx

Breakdown rule, ml, graph, anomaly. rule_flags.
Комментарий. Кнопки PATCH: confirmed, rejected, investigating.""",
    ),
    (
        "3.7 IngestPage",
        """pages/IngestPage.tsx

Форма POST /events: source, user_id, raw_text.
CSV колонки source,user_id,text,url. Batch POST, счётчик.""",
    ),
    (
        "3.8 CORS и сборка VPS",
        """app/main.py — CORSMiddleware allow_origins=*.

Проверка: cd frontend && npm run build → dist/.
Запуск: uvicorn :8000 + npm run dev :5173.""",
    ),
]


def main() -> None:
    for bead_id, title, desc in UPDATES:
        run("update", bead_id, "--title", title, "-d", desc)
        run("close", bead_id, "--reason", "выполнено на VPS")
        print(f"updated {bead_id}")

    for title, desc in CREATES:
        new_id = run(
            "create",
            title,
            "--parent",
            PARENT,
            "-t",
            "task",
            "-p",
            "2",
            "-d",
            desc,
            "--silent",
        )
        run("close", new_id, "--reason", "выполнено на VPS")
        print(f"created {new_id} {title}")

    print("--- children ---")
    print(run("children", PARENT))


if __name__ == "__main__":
    main()
