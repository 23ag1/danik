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

## Dev Notes

### Telegram-сбор без авторизации (t.me/s/)
- **Что:** публичные TG-каналы читаются через веб-превью `https://t.me/s/<канал>` — без Telethon, API-ключей и входа по телефону.
- **Файлы:** `app/collectors/telegram_web.py` (парсер + ingest), `app/collectors/__init__.py` (`collect_source` — диспетчер по `source_type`).
- **Как работает:** TG-источники идут через тот же планировщик, что и RSS (`_run_due_sources` → `collect_source`). Новый канал собирается на следующем тике (≤60с) или мгновенно по кнопке «Запросить» — **без перезапуска сервера**.
- **Парсинг:** регулярки по `data-post="chan/ID"` (дедуп) и `tgme_widget_message_text` (текст). Зависимостей не добавляли.
- **Старый Telethon** (`app/collectors/telegram.py`) оставлен как опциональный, но из планировщика отключён (требовал телефон+код и падал в systemd).

### ML-модель: реальный датасет (спам/скам vs норма)
- **Датасет:** база — `alt-gnome/telegram-spam` (HuggingFace, ~21k реальных русских телеграм-сообщений) + ручная аугментация: финансовый фишинг в spam и реклама/новости в ham (`scripts/build_dataset.py` → `data/fraud_train.csv`). Пересборка: `pip install huggingface_hub pyarrow && python scripts/build_dataset.py`.
- **Модель:** TF-IDF `char_wb` (2-4 грамм) + LogisticRegression — char-граммы устойчивы к обфускации спама (латиница вперемешку: «зapaбoтoк»). Метрики на hold-out: precision ~1.0, recall ~0.98, f1 ~0.99.
- **Зачем так:** старая модель училась на 50 банковских фразах → шумела ~0.5 на всём, реклама = «скам». Теперь реклама/новости (включая финансовые) → 0.02–0.17 (не инцидент), скам → 0.3–0.6.
- **Правила (`FRAUD_KEYWORDS`)** обрезаны до однозначно мошеннических слов (мошенник, разблокир, без вложени…). Общие финансовые (кредит/счёт/процент) и рекламные (розыгрыш/приз/бесплатно) УБРАНЫ — они давали ложные срабатывания на легальных финновостях. ML — первичный сигнал.
- **Аномалия** (`detection._anomaly_stub`) считает реальные сигналы (КАПС, спам «!», телефон/ссылка), а НЕ длину текста.

### Recall-first (главный приоритет — не пропускать мошенничество)
- **Датасет:** `scripts/build_dataset.py` генерирует ~400 вариативных русских фишинг/скам-примеров по шаблонам (счёт заблокирован, приз-фишинг, СМС-код, фейк-выплаты, посылка/таможня, инвест, фейк-кредит, взлом) — готового русского фишинг-датасета в открытом доступе нет. База — alt-gnome/telegram-spam (21k).
- **Порог инцидента развязан с severity:** `settings.incident_threshold = 0.2` (создание инцидента) НИЖЕ `risk_threshold_low = 0.3` (граница severity). Пограничные 0.2–0.3 → инцидент с severity «low» = «на проверку, низкая уверенность». Реальный скам ≥0.3 → medium/high.
- **`FRAUD_KEYWORDS` снова широкий** (recall-net): однозначно мошеннические + финансовая/рекламная лексика. Даёт ложные срабатывания на финновостях — это сознательный компромисс (FN недопустим, FP терпим).
- **Проверка:** на тест-наборе из 14 разнотипных скамов recall = 100% при пороге 0.2; легит-новости/реклама ≤0.17.
