#!/usr/bin/env bash
# Запуск с локальной машины: bash scripts/deploy_phase4.sh
set -euo pipefail
HOST=new-clawd-vps
ROOT=/root/danik/fraud_monitor
LOCAL="$(cd "$(dirname "$0")/.." && pwd)"

scp "$LOCAL/app/main.py" "$HOST:$ROOT/app/main.py"
scp "$LOCAL/requirements.txt" "$LOCAL/README.md" "$HOST:$ROOT/"
scp "$LOCAL/data/demo_events.csv" "$HOST:$ROOT/data/"
scp "$LOCAL/scripts/seed_demo.py" "$LOCAL/scripts/start.sh" "$HOST:$ROOT/scripts/"
scp "$LOCAL/frontend/src/shared/api.ts" "$HOST:$ROOT/frontend/src/shared/"
scp "$LOCAL/frontend/vite.config.ts" "$HOST:$ROOT/frontend/"

ssh "$HOST" "cd $ROOT && chmod +x scripts/*.sh && \
  .venv/bin/pip install -q pytest-cov && \
  cd frontend && npm run build && cd .. && \
  .venv/bin/python -m pytest -q && \
  .venv/bin/python -m pytest --cov=app --cov-report=term-missing -q | tail -15 && \
  pkill -f 'uvicorn app.main:app.*8888' 2>/dev/null || true && \
  .venv/bin/python scripts/seed_demo.py && \
  bd update fraud_monitor-0v3 --claim && \
  bd close fraud_monitor-0v3 --reason 'README, demo seed, static UI, coverage, swagger'"

echo "Готово: http://62.238.0.62:8888"
