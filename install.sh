#!/usr/bin/env bash
set -euo pipefail

echo "=== Fraud Monitor — установка ==="

# Проверить зависимости
command -v python3 >/dev/null || { echo "Нужен Python 3.10+"; exit 1; }
command -v node >/dev/null || { echo "Нужен Node.js 18+"; exit 1; }
command -v npm >/dev/null || { echo "Нужен npm"; exit 1; }

cd "$(dirname "$0")"

# Python окружение
if [ ! -f .venv/bin/activate ]; then
  echo "--- создаю .venv ---"
  python3 -m venv .venv
fi
source .venv/bin/activate

echo "--- pip install ---"
pip install -q -r requirements.txt

# ML модель
if [ ! -f models/fraud_pipeline.joblib ]; then
  echo "--- обучаю ML модель (1-2 мин) ---"
  python -m app.ml.train
else
  echo "--- ML модель уже есть ---"
fi

# Фронтенд
if [ ! -d frontend/dist ]; then
  echo "--- сборка фронтенда ---"
  cd frontend && npm install --silent && npm run build && cd ..
else
  echo "--- фронтенд уже собран ---"
fi

# Демо-данные
echo "--- запускаю сервер для seed ---"
pkill -f 'uvicorn app.main:app' 2>/dev/null || true
sleep 1
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8888 &
SRV_PID=$!

for i in $(seq 1 15); do
  curl -sf http://127.0.0.1:8888/health >/dev/null 2>&1 && break
  sleep 1
done

python scripts/seed_demo.py http://127.0.0.1:8888
python scripts/seed_sources.py

kill $SRV_PID 2>/dev/null || true
sleep 1

# Финальный запуск
PORT=${PORT:-8888}
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT" > /tmp/fraud_monitor.log 2>&1 &

echo ""
echo "======================================"
echo " Fraud Monitor запущен!"
echo " http://localhost:${PORT}"
echo " Swagger: http://localhost:${PORT}/docs"
echo " Log: tail -f /tmp/fraud_monitor.log"
echo "======================================"
