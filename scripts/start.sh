#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PORT=${PORT:-8888}

source .venv/bin/activate

[ -f models/fraud_pipeline.joblib ] || python -m app.ml.train
[ -d frontend/dist ] || (cd frontend && npm install --silent && npm run build)

pkill -f "uvicorn app.main:app.*${PORT}" 2>/dev/null || true
sleep 1
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT" > /tmp/fraud_monitor.log 2>&1 &

echo "Fraud Monitor: http://$(hostname -I | awk '{print $1}'):${PORT}"
echo "Swagger:       http://$(hostname -I | awk '{print $1}'):${PORT}/docs"
echo "Log:           tail -f /tmp/fraud_monitor.log"
