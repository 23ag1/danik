# REST API

Базовый URL: `http://<host>:8000`  
Интерактивная документация: `/docs`

## Health

### `GET /health`

```json
{ "status": "ok" }
```

## Events

### `POST /events`

Приём одного события. Запускает полный пайплайн; при `severity` ≠ `low` создаётся инцидент.

**Body (JSON):**

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| source | string | да | Источник (telegram, vk, csv, …) |
| user_id | string | да | Идентификатор автора (хэшируется в БД) |
| raw_text | string | нет | Текст сообщения |
| url | string | нет | Ссылка в сообщении |
| meta | object | нет | Произвольные метаданные |

**Response 201:**

| Поле | Описание |
|------|----------|
| id | ID события |
| author_hash | SHA-256 от user_id |
| clean_text | Текст после предобработки |
| risk_score | Итоговый риск 0..1 |
| severity | low \| medium \| high |
| incident_id | ID инцидента или null |

## Incidents

### `GET /incidents`

Список инцидентов, сортировка по `created_at` desc.

### `PATCH /incidents/{incident_id}/status`

Обновление статуса аналитиком (human-in-the-loop).

**Body:**

```json
{
  "status": "confirmed",
  "analyst_comment": "Подтверждён фишинг"
}
```

**status:** `new` | `investigating` | `confirmed` | `rejected`

Пишет запись в `audit_logs`.

## CSV (через UI, не отдельный endpoint)

Формат файла:

```csv
source,user_id,text,url
telegram,user123,Срочно переведите деньги,https://evil.example
```

Каждая строка → отдельный `POST /events`.
