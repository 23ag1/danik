# Fraud Monitor — обзор проекта (для написания диплома)

> Скопируйте этот файл целиком в ChatGPT/Claude при работе над главой 3 (реализация) и экспериментальной частью.

## 1. Назначение

**Fraud Monitor** — учебный прототип системы мониторинга сообщений из социальных сетей для выявления признаков мошенничества в контексте кредитно-финансовых организаций.

- Направление: **10.03.01 Информационная безопасность**
- Тема: алгоритм мониторинга соцсетей по противодействию мошенничеству
- Реализация: **гибридный пайплайн** (правила + ML + граф связей + эвристика аномалий) + веб-интерфейс аналитика

**Важно:** реального парсинга VK/Twitter нет. Данные поступают через **REST API** и **загрузку CSV** (имитация внешних источников).

## 2. Технологический стек

| Слой | Технологии |
|------|------------|
| Backend | Python 3.11+, **FastAPI**, **SQLAlchemy 2 (async)**, **SQLite** (aiosqlite), **Alembic** |
| ML | **scikit-learn** (Pipeline: TF-IDF + LogisticRegression), **joblib** |
| Граф | **NetworkX** (in-memory граф авторов) |
| Frontend | **React 18**, **TypeScript**, **Vite**, **Tailwind CSS**, React Router |
| Тесты | **pytest**, pytest-asyncio, pytest-cov (цель ≥70%) |
| Деплой | uvicorn, `scripts/start.sh`, статика из `frontend/dist` |

Не используются: Django, Celery, Redis, PostgreSQL (упрощение для дипломного прототипа).

## 3. Архитектура обработки

```
Ввод (POST /events или CSV)
    → preprocessing (нормализация, маски PII)
    → features (структурные признаки текста)
    → detection (rules + ML + anomaly stub)
    → graph (связи авторов по rule_flags)
    → scoring (взвешенная сумма → severity)
    → incident (если severity ≠ low)
    → UI аналитика (подтверждение / отклонение)
```

### Формула риска

`S = 0.35·rule + 0.35·ml + 0.15·graph + 0.15·anomaly` (веса в `app/config.py`)

### Пороги severity

| Risk score | Severity | Поведение |
|------------|----------|-----------|
| &lt; 0.3 | low | Инцидент не создаётся |
| 0.3 – 0.7 | medium | Создаётся инцидент для проверки |
| ≥ 0.7 | high | Создаётся инцидент (приоритетный) |

## 4. Структура репозитория

```
fraud_monitor/
├── app/
│   ├── main.py              # FastAPI, CORS, StaticFiles, /health
│   ├── config.py            # pydantic-settings, веса риска
│   ├── database.py          # async engine, create_tables
│   ├── utils.py             # SHA256(user_id) → author_hash
│   ├── models/              # Event, Incident, AuditLog
│   ├── schemas/             # Pydantic request/response
│   ├── routers/             # events, incidents
│   ├── pipeline/            # preprocessing, features, detection, scoring, graph
│   ├── services/            # pipeline_runner (оркестрация)
│   └── ml/                  # train, model, dataset, metrics
├── frontend/src/            # React UI
├── alembic/                 # миграции БД
├── data/                    # fraud_train.csv, demo_events.csv
├── scripts/                 # start.sh, seed_demo.py, finish_phase4.sh
├── tests/                   # pytest (API, pipeline, ML, graph)
├── docs/                    # документация для диплома
├── CLAUDE.md                # правила для агента разработки
└── requirements.txt
```

## 5. Реализованные функции

### 5.1 Приём данных

- `POST /events` — одно событие (source, user_id, raw_text, url?, meta?)
- UI **Загрузка**: ручной ввод + пакетная отправка CSV (`source,user_id,text,url`)
- Скрипт `scripts/seed_demo.py` — наполнение демо-данными

### 5.2 Предобработка и приватность

- `user_id` → **SHA-256** (`author_hash`), сырой ID не хранится в открытом виде в логике скоринга
- Маски в тексте: `<PHONE>`, `<EMAIL>`, `<URL>`
- Lowercase, схлопывание пробелов

### 5.3 Детекция (гибрид)

1. **Правила** — список ключевых слов мошенничества (кредит, займ, срочно, …), score = min(1, 0.2 × число совпадений)
2. **ML** — LogReg + TF-IDF на `data/fraud_train.csv`; артефакты `models/fraud_pipeline.joblib`
3. **Граф** — авторы как узлы; рёбра при пересечении `rule_flags`; score от степени и соседей
4. **Аномалии** — эвристика по длине текста, числу слов, восклицательным знакам

### 5.4 Инциденты и human-in-the-loop

- Автосоздание `Incident` при medium/high severity
- `GET /incidents` — список
- `PATCH /incidents/{id}/status` — статусы: `new`, `investigating`, `confirmed`, `rejected` + `analyst_comment`
- **AuditLog** в БД при ingest и смене статуса

### 5.5 Веб-интерфейс аналитика

| Страница | URL | Функции |
|----------|-----|---------|
| Сводка | `/` | KPI: всего инцидентов, новых, high, средний risk |
| Инциденты | `/incidents` | Таблица, фильтр по status/severity, поиск |
| Карточка | `/incidents/:id` | Разбивка rule/ml/graph/anomaly, флаги, кнопки подтвердить/отклонить |
| Загрузка | `/ingest` | Форма + CSV |

### 5.6 API и документация

- Swagger: `/docs`, ReDoc: `/redoc`
- `GET /health` — проверка живости

## 6. База данных (SQLite)

| Таблица | Назначение |
|---------|------------|
| `events` | Сырые/очищенные сообщения, source, author_hash |
| `incidents` | Риск, severity, статус, скоры, rule_flags, комментарий |
| `audit_logs` | action, entity_type, entity_id, details (JSON) |

Миграции: Alembic (`alembic/versions/`).

## 7. ML: обучение и метрики

```bash
python -m app.ml.train
```

- Датасет: `data/fraud_train.csv` (текст + метка 0/1)
- Модель: `TfidfVectorizer` + `LogisticRegression`
- Метрики: precision, recall, F1 (`app/ml/metrics.py`)
- Целевые пороги проекта: F1 ≥ 0.68, precision ≥ 0.70

## 8. Тестирование

```bash
pytest -q
pytest --cov=app --cov-report=term-missing -q
```

Покрытие: preprocessing, features, detection, scoring, graph, ML, API (events/incidents), модели ORM.

## 9. Запуск на VPS

```bash
cd /root/danik/fraud_monitor
source .venv/bin/activate
pip install -r requirements.txt
python -m app.ml.train
cd frontend && npm install && npm run build
bash scripts/start.sh
# http://<IP>:8000
```

## 10. Соответствие диплому (главы 1–2)

| Требование из текста | Статус в прототипе |
|----------------------|-------------------|
| Модульный пайплайн сбор→обработка→детекция→скоринг | ✅ |
| Гибрид: правила + ML + граф + аномалии | ✅ |
| Пороги low/medium/high (0.3, 0.7) | ✅ |
| Human-in-the-loop (аналитик) | ✅ частично (нет переобучения по feedback) |
| Анонимизация / маски PII | ✅ |
| Журнал аудита | ✅ в БД, без UI |
| REST API | ✅ |
| Реальный API соцсетей, TI-фиды | ❌ (CSV/API заглушка) |
| SHAP/LIME, PDF-отчёты, push-уведомления | ❌ |
| Переобучение по меткам аналитика | ❌ (перспектива) |

Подробнее: `docs/DIPLOMA-ALIGNMENT.md`.

## 11. Ограничения и перспектива (для «Выводов»)

1. Прототип ориентирован на **демонстрацию алгоритма**, не на промышленную нагрузку.
2. Граф хранится **в памяти** процесса (NetworkX), не в отдельном graph DB.
3. Веса скоринга **фиксированы** в конфиге, адаптация по feedback не реализована.
4. Для production потребуются: очередь сообщений, PostgreSQL, RBAC, внешние коннекторы, мониторинг SLA.

## 12. Ключевые файлы для цитирования в дипломе

- Пайплайн: `app/services/pipeline_runner.py`
- Правила: `app/pipeline/detection.py`
- Скоринг: `app/pipeline/scoring.py`
- Граф: `app/pipeline/graph.py`
- API ingest: `app/routers/events.py`
- API аналитика: `app/routers/incidents.py`
- Конфиг: `app/config.py`
