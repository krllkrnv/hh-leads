# HH Leads

Дашборд и CLI для разбора переписок с работодателями на [hh.ru](https://hh.ru). Чаты забираются через Chatik API, лиды классифицируются и показываются в интерфейсе или выгружаются в Excel.

## Онлайн

**→ [https://hh-leads.onrender.com/](https://hh-leads.onrender.com/)**

Рабочий деплой дашборда. После простоя на free-плане Render первый заход может занять подольше — сервис прогревается.

В дашборде два режима:

1. **Sync** — cookie из браузера и период в днях → отчёт из чатов hh.
2. **Upload** — готовый `.json` или `.xlsx`, скачанный из этого же дашборда раньше.

Период «N дней» учитывает **последнюю активность** в чате, не дату отклика.

## Cookie

1. Открыть [hh.ru](https://hh.ru) и войти в аккаунт.
2. F12 → **Network**, обновить страницу, выбрать любой запрос к `hh.ru`.
3. В **Request Headers** скопировать значение **Cookie** (без слова `Cookie:`). Подойдёт и JSON **Request Cookies** из DevTools.
4. В дашборде вставить текст в форму. Для CLI — записать в `.env` как `HH_COOKIE=...`.

Нужны как минимум `hhtoken` и `_xsrf`. В дашборде cookie остаётся только в поле формы на время sync; на диск сервер его не пишет.

## Локально

```bash
cd hh_chats
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

cd web && npm install && cd ..
```

### API и фронт в двух терминалах (с hot reload)

В одном терминале — бэкенд, во втором — Vite. Скрипты:

```bash
./scripts/dev.sh api
./scripts/dev.sh web
```

Дашборд: http://127.0.0.1:5173 (проксирует API на порт 8000).

Те же два сервиса без `dev.sh`:

```bash
source .venv/bin/activate
uvicorn hh_leads.api:app --reload --host 127.0.0.1 --port 8000

cd web && npm run dev
```

### Сборка фронта и один процесс API

Фронт собирается в статику, API отдаёт её с порта 8000:

```bash
cd web && npm run build && cd ..
source .venv/bin/activate
uvicorn hh_leads.api:app --host 127.0.0.1 --port 8000
```

Адрес: http://127.0.0.1:8000

### Docker

```bash
docker compose up --build
```

Адрес: http://127.0.0.1:8000

## CLI → Excel

```bash
source .venv/bin/activate
python analyze_chats.py
python analyze_chats.py --days 60 --out report.xlsx
python analyze_chats.py --cookie "hhtoken=...; _xsrf=..."
```

В файле листы: Сводка, Действия, Приглашения, Тестовые, Обсуждения, Все действия. Этот Excel можно снова открыть в дашборде через Upload.

## API

| Метод | Путь | Назначение |
|-------|------|------------|
| `POST` | `/api/sync` | sync по cookie |
| `POST` | `/api/sync/stream` | sync + NDJSON прогресс |
| `POST` | `/api/sync/cancel` | остановить sync (`X-Session-Id`) |
| `POST` | `/api/upload` | `.xlsx` / `.json` |
| `POST` | `/api/upload/stream` | upload + прогресс |
| `GET` | `/api/report` | текущий отчёт |
| `GET` | `/api/report/excel` | скачать Excel |
| `DELETE` | `/api/session` | очистить сессию |
| `GET` | `/api/health` | healthcheck |

## Тесты

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
ruff check .
```

## Классификация

По текстам работодателя и статусам `invitation` / `interview`.

| Категория | Как определяется |
|-----------|------------------|
| Приглашения | Собес, звонок, telegram и т.п., либо статус invitation/interview |
| Тестовые | Тестовое / case / homework |
| Обсуждения | Остальные чаты с перепиской |
| Действия | Ответить / ждать / бот / закрыто — по тексту и тому, кто писал последним |

## Ограничения

- Cookie со временем протухают — при 401/403 нужна свежая копия из браузера.
- Chatik API не официальный контракт hh и может меняться.
- Только чтение: сообщения не отправляются.
- Отчёт сессии живёт в памяти процесса — после рестарта или «сна» Render нужна новая sync или upload файла.
- Если sync остановить раньше времени, в отчёт попадут уже разобранные чаты.
