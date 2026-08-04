# HH Leads — CLI + локальный дашборд

Инструмент для соискателя: забирает переписки hh.ru через Chatik API, классифицирует лиды и показывает их в локальном веб-дашборде (или Excel через CLI).

**Только для себя на localhost.** Cookie = полный доступ к аккаунту hh. Не выкладывайте cookie в репозиторий и не поднимайте сервис в публичный интернет.

## Подготовка

```bash
cd hh_chats
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # только для CLI-удобства
```

Фронт (один раз):

```bash
cd web
npm install
```

### Как получить cookie

1. Открой [hh.ru](https://hh.ru) и войди (SMS).
2. F12 → **Network**.
3. Обнови страницу, кликни любой запрос к `hh.ru`.
4. В **Request Headers** скопируй значение `Cookie` (без слова `Cookie:`).
5. Для CLI — вставь в `.env` как `HH_COOKIE=...`. Для дашборда — вставь в UI (в память процесса / `sessionStorage`, на диск не пишется).

В cookie нужны как минимум `hhtoken` и `_xsrf`.

## Веб-дашборд

Два режима данных:

1. **Sync** — cookie + число дней → Chatik API → отчёт в памяти сессии.
2. **Upload** — свой `.xlsx` (выгрузка CLI) или `.json` (ранее сохранённый отчёт дашборда).

### Dev (два процесса)

Терминал 1 — API:

```bash
cd hh_chats
./scripts/dev.sh api
# или: source .venv/bin/activate && uvicorn api:app --reload --port 8000
```

Терминал 2 — Vite (проксирует `/api` на `:8000`):

```bash
cd hh_chats
./scripts/dev.sh web
# или: cd web && npm run dev
```

Открой http://127.0.0.1:5173

### Prod (статика из FastAPI)

```bash
cd hh_chats/web && npm run build
cd ..
source .venv/bin/activate
uvicorn api:app --port 8000
```

Открой http://127.0.0.1:8000

### API

| Метод | Путь | Назначение |
|-------|------|------------|
| `POST` | `/api/sync` | `{ cookie, days, hhHost? }` → отчёт |
| `POST` | `/api/upload` | multipart `.xlsx` / `.json` |
| `GET` | `/api/report` | текущий отчёт (заголовок `X-Session-Id`) |
| `DELETE` | `/api/session` | очистить сессию |
| `GET` | `/api/health` | healthcheck |

## CLI (как раньше)

```bash
python analyze_chats.py
python analyze_chats.py --days 60 --out report.xlsx
python analyze_chats.py --cookie "hhtoken=...; _xsrf=..."
```

Результат: Excel с листами **Сводка**, **Действия**, **Приглашения**, **Тестовые**, **Обсуждения**, **Все действия**. Этот же файл можно загрузить в дашборд без cookie.

## Классификация

По содержанию сообщений работодателя плюс мягкий сигнал статуса `invitation`/`interview`. Паттерны широкие: лучше лишний чат в приглашениях, чем пропущенный лид.

| Категория | Как определяется |
|-----------|------------------|
| Приглашения | Текст про собес/звонок/напишите/telegram и т.п., либо статус invitation/interview |
| Тестовые | Текст про тестовое / case / homework |
| Обсуждения | Остальные чаты с перепиской |
| Действия | Признаки в тексте + кто писал последним |

## Структура

| Модуль | Назначение |
|--------|------------|
| `hh_client.py` | HTTP к Chatik |
| `classify.py` | чистая классификация |
| `report.py` | модель отчёта + Excel |
| `pipeline.py` | sync pipeline |
| `cli.py` / `analyze_chats.py` | CLI |
| `api.py` | FastAPI |
| `web/` | Vue 3 + Vite + TS + SCSS |

## Ограничения

- Cookie живут ограниченное время — при 401/403 скопируй заново.
- Chatik API не официальный контракт, может меняться.
- Только чтение; сообщения не отправляются.
- Single-user, in-memory сессии — перезапуск API сбрасывает данные (загрузите файл снова или сделайте sync).
