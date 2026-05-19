#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

[ -f models/fraud_pipeline.joblib ] || python -m app.ml.train
[ -d frontend/dist ] || (cd frontend && npm install --silent && npm run build)

pkill -f 'uvicorn app.main:app.*8000' 2>/dev/null || true
sleep 1
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/fraud_monitor.log 2>&1 &
echo "Fraud Monitor: http://$(hostname -I | awk '{print $1}'):8000"
echo "Swagger: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "log: /tmp/fraud_monitor.log"
