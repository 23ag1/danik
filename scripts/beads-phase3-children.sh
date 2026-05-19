#!/usr/bin/env bash
set -euo pipefail
cd /root/danik/fraud_monitor
PARENT=fraud_monitor-6q0

bd update "$PARENT" -d "$(cat <<'EOF'
Фаза 3: React SPA для аналитика (учебный проект, без overengineering).

ЦЕЛЬ
Список инцидентов с фильтрами, карточка, Подтвердить/Отклонить/В работу, ручной ввод и CSV, сводка.

СТЕК
Vite + React 18 + TypeScript + Tailwind v4 + React Router.
Без TanStack Query, Framer, shadcn, отдельного widgets-слоя.

СТРУКТУРА (FSD-lite)
frontend/src/
  app/App.tsx           — router
  shared/api.ts         — fetch /api/*
  shared/types.ts
  shared/ui/Layout.tsx, Badge.tsx
  pages/                — Dashboard, Incidents, IncidentDetail, Ingest

API БЭКЕНДА
GET  /incidents
PATCH /incidents/{id}/status  { status, analyst_comment? }
POST /events  { source, user_id, raw_text, url? }
CSV → парсинг на клиенте → N× POST /events

ДИЗАЙН
Zinc + teal accent, DM Sans + IBM Plex Mono для цифр.
Без Inter, без purple gradients, без emoji.

ЗАПУСК НА VPS
source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000
cd frontend && npm install && npm run dev    # :5173, proxy /api → :8000
cd frontend && npm run build                   # dist/

CORS: app/main.py — CORSMiddleware allow_origins=*

ДОЧЕРНИЕ ЗАДАЧИ: 3.1–3.7 (см. bd children fraud_monitor-6q0)
EOF
)"

mk() {
  local title="$1"
  local desc="$2"
  local id
  id=$(bd create "$title" --parent "$PARENT" -t task -p 2 -d "$desc" --silent)
  bd close "$id" --reason "выполнено на VPS"
  echo "created $id — $title"
}

mk "3.1 План и docs" "$(cat <<'EOF'
docs/frontend-architecture.md — краткая схема слоёв и команд запуска.
Решения: FSD-lite (shared+pages+app), без enterprise-слоёв.
EOF
)"

mk "3.2 Scaffold frontend" "$(cat <<'EOF'
frontend/: package.json, vite.config.ts (proxy /api → :8000), tailwind, tsconfig.
index.html, src/main.tsx, src/index.css (@theme fonts).
Команды: npm install, npm run dev, npm run build.
EOF
)"

mk "3.3 shared: api, types, ui" "$(cat <<'EOF'
shared/types.ts — Incident, EventCreate, Severity, IncidentStatus.
shared/api.ts — getIncidents, patchIncident, createEvent, health (BASE=/api).
shared/ui/Layout.tsx — nav: Сводка, Инциденты, Загрузка.
shared/ui/Badge.tsx — severity/status цвета.
EOF
)"

mk "3.4 DashboardPage" "$(cat <<'EOF'
pages/DashboardPage.tsx
GET /incidents → KPI: всего, новых (status=new), high severity, средний risk.
Блок «Последние» (до 8) со ссылками на /incidents/:id.
Empty → ссылка на /ingest.
EOF
)"

mk "3.5 IncidentsPage" "$(cat <<'EOF'
pages/IncidentsPage.tsx
Таблица: id, title, risk_score, severity, status.
Фильтры client-side: status, severity, поиск по title.
Ссылки на /incidents/:id.
EOF
)"

mk "3.6 IncidentDetailPage" "$(cat <<'EOF'
pages/IncidentDetailPage.tsx
Данные из списка по id. Разбивка: rule/ml/graph/anomaly (progress).
rule_flags тегами. textarea комментарий.
Кнопки → PATCH: confirmed, rejected, investigating.
EOF
)"

mk "3.7 IngestPage" "$(cat <<'EOF'
pages/IngestPage.tsx
Форма: source, user_id, raw_text → POST /events.
CSV: source,user_id,text,url — первая строка header если starts with source.
Batch POST, лог «отправлено N».
EOF
)"

mk "3.8 CORS и сборка на VPS" "$(cat <<'EOF'
app/main.py — CORSMiddleware.
Проверка: cd frontend && npm run build (dist/).
uvicorn + npm run dev для ручной проверки UI.
EOF
)"

echo "--- children ---"
bd children "$PARENT"
