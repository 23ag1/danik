#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

chmod +x scripts/*.sh
pip install -q -r requirements.txt
[ -f models/fraud_pipeline.joblib ] || python -m app.ml.train

cd frontend && npm install --silent && npm run build && cd ..

python -m pytest -q
python -m pytest --cov=app --cov-fail-under=70 -q

pkill -f 'uvicorn app.main:app.*8888' 2>/dev/null || true
sleep 1
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8888 > /tmp/fraud_monitor.log 2>&1 &
for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -sf http://127.0.0.1:8888/health >/dev/null && break
  sleep 1
done

python scripts/seed_demo.py http://127.0.0.1:8888

echo "--- checks ---"
curl -sf http://127.0.0.1:8888/health && echo
curl -sf http://127.0.0.1:8888/incidents | python3 -c "import sys,json; d=json.load(sys.stdin); print('incidents:', len(d))"
curl -sf -o /dev/null -w "docs HTTP %{http_code}\n" http://127.0.0.1:8888/docs
curl -sf -o /dev/null -w "ui HTTP %{http_code}\n" http://127.0.0.1:8888/
