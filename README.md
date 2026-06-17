# Fraud Monitor

Дипломная работа (10.03.01 ИБ): мониторинг сообщений и выявление мошенничества.

**Стек:** FastAPI · SQLAlchemy · SQLite · scikit-learn · NetworkX · React · Vite

## Документация

| Файл | Содержание |
|------|------------|
| [docs/PROJECT-OVERVIEW.md](docs/PROJECT-OVERVIEW.md) | Полный обзор: стек, фичи, пайплайн, структура |
| [docs/API.md](docs/API.md) | REST API |
| [docs/DIPLOMA-ALIGNMENT.md](docs/DIPLOMA-ALIGNMENT.md) | Соответствие главам 1–2 диплома |
| [docs/frontend-architecture.md](docs/frontend-architecture.md) | Фронтенд |

## Требования

- Python 3.10+
- Node.js 18+
- Git

## Быстрый старт

```bash
git clone <repo-url>
cd fraud_monitor

# 1. Python-окружение
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Обучить ML-модель (один раз)
python -m app.ml.train

# 3. Запустить (собирает фронт + стартует сервер)
bash scripts/start.sh
```

Приложение будет доступно на **http://localhost:8888**  
Swagger API: **http://localhost:8888/docs**

> Порт можно изменить: `PORT=9000 bash scripts/start.sh`

## Демо-данные

```bash
python scripts/seed_demo.py          # инциденты и события
python scripts/seed_sources.py       # RSS-источники
```

## Режим разработки (hot reload)

Запустить бэкенд и фронт отдельно:

```bash
# Терминал 1 — бэкенд
source .venv/bin/activate
uvicorn app.main:app --reload --port 8888

# Терминал 2 — фронтенд (dev server + proxy на :8888)
cd frontend
npm install
npm run dev
# открыть http://localhost:5173
```

## Тесты

```bash
source .venv/bin/activate
python -m pytest -q
python -m pytest --cov=app --cov-report=term-missing -q
```

## Переменные окружения (опционально)

Создайте `.env` в корне проекта:

```env
DATABASE_URL=sqlite+aiosqlite:///./fraud_monitor.db
# Telegram (если нужен сбор из TG-каналов)
# TG_API_ID=12345
# TG_API_HASH=your_hash
# TG_SESSION_NAME=fraud_monitor_tg
```

## Telegram-сканер (опционально)

Чтобы собирать сообщения из Telegram-каналов:

```bash
# 1. Авторизоваться (один раз, потребует номер телефона)
python scripts/auth_tg.py

# 2. Добавить канал через API или UI (Источники → Добавить → Telegram)
# 3. Перезапустить сервер
```
