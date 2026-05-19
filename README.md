# Fraud Monitor

Дипломная работа (10.03.01 ИБ): мониторинг сообщений и выявление мошенничества.

**Стек:** FastAPI · SQLAlchemy · SQLite · scikit-learn · NetworkX · React · Vite

## Документация (для диплома и GPT)

| Файл | Содержание |
|------|------------|
| [docs/PROJECT-OVERVIEW.md](docs/PROJECT-OVERVIEW.md) | Полный обзор: стек, фичи, пайплайн, структура |
| [docs/API.md](docs/API.md) | REST API |
| [docs/DIPLOMA-ALIGNMENT.md](docs/DIPLOMA-ALIGNMENT.md) | Соответствие главам 1–2 диплома |
| [docs/frontend-architecture.md](docs/frontend-architecture.md) | Фронтенд |
| [CLAUDE.md](CLAUDE.md) | Правила разработки для агента |

## Быстрый старт (VPS)

```bash
cd /root/danik/fraud_monitor
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.ml.train
cd frontend && npm install && npm run build && cd ..
bash scripts/start.sh
# http://<IP>:8000  ·  Swagger: /docs
```

Демо-данные: `python scripts/seed_demo.py`

## Тесты

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest --cov=app --cov-report=term-missing -q
```

## Публикация на GitHub

На сервере (где настроен `gh auth login`):

```bash
bash scripts/push_to_github.sh danik private
```
