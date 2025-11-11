Incidents API (FastAPI)
=======================

Маленький API‑сервис учёта инцидентов.

Технологии: FastAPI, SQLAlchemy 2.x, SQLite.

Требования
----------
- Python 3.13+
- Никаких внешних СУБД не требуется — используется SQLite (файл `incidents.db` в корне).

Запуск
------

Вариант A: через uv (рекомендуется, в репозитории есть `uv.lock`)
1) Установите зависимости:
   - `uv sync`
2) Запустите сервер (горячая перезагрузка):
   - `uv run uvicorn main:app --reload`

Вариант B: через pip (без uv)
1) Создайте и активируйте виртуальное окружение:
   - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows (PowerShell): `py -m venv .venv; .\.venv\Scripts\Activate.ps1`
2) Установите зависимости:
   - `pip install "fastapi[standard]" "sqlalchemy>=2.0"`
3) Запустите сервер:
   - `uvicorn main:app --reload`

После запуска API будет доступно на `http://127.0.0.1:8000`.
Интерактивная документация Swagger UI: `http://127.0.0.1:8000/docs`.

Модель инцидента
----------------
- `id` — integer, PK
- `description` — текст/описание
- `status` — один из: `open`, `in_progress`, `resolved`, `closed`
- `source` — строка (например, `operator`, `monitoring`, `partner`)
- `created_at` — UTC datetime

Эндпоинты
---------

1) Создать инцидент
- Method: POST
- Path: `/incidents`
- Body:
```json
{
  "description": "Самокат #42 не в сети",
  "source": "operator",
  "status": "open"
}
```
- Ответ: 201, JSON инцидента

Пример curl:
```bash
curl -X POST http://127.0.0.1:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{"description":"Самокат #42 не в сети","source":"operator"}'
```

2) Получить список инцидентов (с фильтром по статусу)
- Method: GET
- Path: `/incidents`
- Query: `status` (необязательный) — `open|in_progress|resolved|closed`

Примеры:
```bash
curl "http://127.0.0.1:8000/incidents"
curl "http://127.0.0.1:8000/incidents?status=open"
```

3) Обновить статус инцидента по id
- Method: PATCH
- Path: `/incidents/{id}/status`
- Body:
```json
{ "status": "resolved" }
```
- Ответ: 200, JSON инцидента

Пример:
```bash
curl -X PATCH http://127.0.0.1:8000/incidents/1/status \
  -H "Content-Type: application/json" \
  -d '{"status":"resolved"}'
```

Дополнительно
-------------
- Статусы: `open`, `in_progress`, `resolved`, `closed`
- При отсутствии инцидента возвращается 404.


