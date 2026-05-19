# fraud_monitor — Diploma Project

Система мониторинга соцсетей для выявления фрода в кредитно-финансовых организациях.
Дипломная работа, направление 10.03.01 Информационная безопасность.

## Stack
- **Backend**: FastAPI + SQLAlchemy (async) + SQLite + Alembic
- **ML**: scikit-learn (LogReg / RandomForest) + NetworkX (граф)
- **Tasks**: FastAPI BackgroundTasks (без Celery/Redis)
- **Frontend**: React (фаза 3, после бэкенда)
- **Tests**: pytest + pytest-asyncio

## Architecture
```
input (CSV / API) → preprocessing → feature extraction → detection (rules + ML + graph) → scoring → incident
```

Pipeline: `app/pipeline/` — preprocessing.py → features.py → detection.py → scoring.py → graph.py

## Key Files
```
app/
  main.py          — FastAPI app, routers
  config.py        — pydantic-settings (.env)
  database.py      — async SQLAlchemy engine
  models/          — ORM: Event, Incident, AuditLog
  schemas/         — Pydantic: request/response schemas
  routers/         — API endpoints
  pipeline/        — core processing logic
tests/             — pytest, цель покрытия >70%
```

## Risk Scoring Formula
`S(x) = w1·rule + w2·ml + w3·graph + w4·anomaly`
Веса: rule=0.35, ml=0.35, graph=0.15, anomaly=0.15
Пороги: <0.3 low · 0.3–0.7 medium · >0.7 high

## Anonymization
- user_id → SHA256 hash (author_hash)
- Текст: phone → `<PHONE>`, email → `<EMAIL>`, url → `<URL>`

## Beads Tasks
- `fraud_monitor-op0` — Фаза 1: Ядро ✓
- `fraud_monitor-2cb` — Фаза 2: ML + граф ✓
- `fraud_monitor-6q0` — Фаза 3: React фронтенд ✓
- `fraud_monitor-0v3` — Фаза 4: Доводка (запустить scripts/finish_phase4.sh)

## Success Metrics
| | Минимум | Цель |
|---|---|---|
| F1 (ML) | 0.68 | 0.77 |
| Precision | 0.70 | 0.80 |
| Test coverage | 70% | 80% |

## Workflow (MANDATORY)
Каждый bead: план (дочерние beads) → реализация по TDD → /simplify проверка → закрыть bead.
Не закрывать bead пока не прошёл TDD + /simplify. Фронт — только после завершения всего бэкенда.

## Constraints
- Нет реального парсинга соцсетей (ключи API не нужны)
- Данные: CSV загрузка + ручной ввод через API
- Датасет: подбираем (SMS Spam Collection / финансовый фрод с Kaggle)
- Текст диплома можно менять под реализацию
