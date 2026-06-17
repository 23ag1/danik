#!/usr/bin/env bash
# Fraud Monitor — start server
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
PORT=${PORT:-8888}
echo "Fraud Monitor: http://localhost:${PORT}"
echo "Press Ctrl+C to stop."
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
