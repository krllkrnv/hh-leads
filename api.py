"""FastAPI: sync / upload / report / clear session для локального дашборда."""

from __future__ import annotations

import json
import queue
import re
import secrets
import tempfile
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from hh_client import HhApiError, HhAuthError
from pipeline import PartialSync, fetch_records
from progress import ProgressEvent, emit
from report import build_report, records_from_excel, records_from_report, write_excel

ROOT = Path(__file__).resolve().parent
WEB_DIST = ROOT / "web" / "dist"
WEB_DIST_RESOLVED = WEB_DIST.resolve()

MAX_SESSIONS = 32
SESSION_TTL_SEC = 6 * 60 * 60
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


@dataclass
class SessionEntry:
    report: dict[str, Any]
    touched_at: float = field(default_factory=time.time)


# session_id -> report (in-memory, single-user local tool)
_SESSIONS: dict[str, SessionEntry] = {}
_CANCEL: dict[str, threading.Event] = {}
_LOCK = threading.Lock()

app = FastAPI(title="HH Leads Dashboard", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SyncBody(BaseModel):
    cookie: str = Field(min_length=10)
    days: int = Field(default=60, ge=1, le=180)
    hhHost: str | None = None
    delay: float = Field(default=0.25, ge=0.0, le=2.0)


def _prune_sessions() -> None:
    now = time.time()
    expired = [sid for sid, entry in _SESSIONS.items() if now - entry.touched_at > SESSION_TTL_SEC]
    for sid in expired:
        _SESSIONS.pop(sid, None)
        _CANCEL.pop(sid, None)
    while len(_SESSIONS) > MAX_SESSIONS:
        oldest = min(_SESSIONS.items(), key=lambda item: item[1].touched_at)[0]
        _SESSIONS.pop(oldest, None)
        _CANCEL.pop(oldest, None)


def _store_report(sid: str, report: dict[str, Any]) -> None:
    with _LOCK:
        _prune_sessions()
        _SESSIONS[sid] = SessionEntry(report=report)
        _CANCEL.pop(sid, None)


def _get_report(sid: str) -> dict[str, Any] | None:
    with _LOCK:
        entry = _SESSIONS.get(sid)
        if not entry:
            return None
        if time.time() - entry.touched_at > SESSION_TTL_SEC:
            _SESSIONS.pop(sid, None)
            return None
        entry.touched_at = time.time()
        return entry.report


def _session_id(x_session_id: str | None, *, allow_client_mint: bool = False) -> str:
    """Переиспользует известный id; для sync/upload может принять клиентский id для cancel."""
    candidate = (x_session_id or "").strip()
    with _LOCK:
        _prune_sessions()
        if candidate and candidate in _SESSIONS:
            return candidate
        if allow_client_mint and candidate and 16 <= len(candidate) <= 80:
            return candidate
    return secrets.token_urlsafe(16)


def _cancel_event(sid: str) -> threading.Event:
    with _LOCK:
        event = _CANCEL.get(sid)
        if event is None:
            event = threading.Event()
            _CANCEL[sid] = event
        else:
            event.clear()
        return event


def _is_valid_report(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    meta = data.get("meta")
    leads = data.get("leads")
    if not isinstance(meta, dict) or not isinstance(leads, dict):
        return False
    required_lead_keys = ("all", "reply", "interview", "contact", "tests", "invites", "closed")
    return all(key in leads and isinstance(leads[key], list) for key in required_lead_keys)


def _ndjson_line(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


def _stream_job(worker: Any) -> Iterator[str]:
    """Запускает worker(put_event) в потоке и стримит NDJSON из очереди."""
    events: queue.Queue[dict[str, Any] | None] = queue.Queue()

    def put_event(payload: dict[str, Any]) -> None:
        events.put(payload)

    def run() -> None:
        try:
            worker(put_event)
        except Exception as exc:  # noqa: BLE001
            put_event({"type": "error", "message": str(exc)})
        finally:
            events.put(None)

    threading.Thread(target=run, daemon=True).start()
    while True:
        item = events.get()
        if item is None:
            break
        yield _ndjson_line(item)


def _safe_dist_file(full_path: str) -> Path | None:
    """Возвращает файл внутри WEB_DIST или None (защита от path traversal)."""
    candidate = (WEB_DIST / full_path).resolve()
    try:
        candidate.relative_to(WEB_DIST_RESOLVED)
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sync")
def sync(body: SyncBody, x_session_id: str | None = Header(default=None)) -> dict[str, Any]:
    sid = _session_id(x_session_id, allow_client_mint=True)
    cancel = _cancel_event(sid)
    try:
        records, since = fetch_records(
            body.cookie,
            body.days,
            delay=body.delay,
            hh_host=body.hhHost,
            should_cancel=cancel.is_set,
        )
        incomplete = False
    except PartialSync as partial:
        records, since = partial.records, partial.since
        incomplete = True
    except HhAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except HhApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Синхронизация не удалась: {exc}") from exc

    report = build_report(
        records,
        days=body.days,
        since=since,
        source="sync",
        incomplete=incomplete,
    )
    _store_report(sid, report)
    return {"sessionId": sid, "report": report}


@app.post("/api/sync/stream")
def sync_stream(
    body: SyncBody,
    x_session_id: str | None = Header(default=None),
) -> StreamingResponse:
    sid = _session_id(x_session_id, allow_client_mint=True)
    cancel = _cancel_event(sid)

    def worker(put_event: Any) -> None:
        def on_progress(event: ProgressEvent) -> None:
            put_event({"type": "progress", "sessionId": sid, **event})

        try:
            records, since = fetch_records(
                body.cookie,
                body.days,
                delay=body.delay,
                hh_host=body.hhHost,
                on_progress=on_progress,
                should_cancel=cancel.is_set,
            )
            incomplete = False
            done_msg = "Готово — отчёт собран"
        except PartialSync as partial:
            records, since = partial.records, partial.since
            incomplete = True
            done_msg = (
                f"Остановили раньше времени: в отчёте {len(records)} уже разобранных чатов"
                if records
                else "Остановили до того, как успели разобрать хотя бы один чат"
            )
            emit(on_progress, "warn", done_msg)
        except HhAuthError as exc:
            put_event({"type": "error", "sessionId": sid, "message": str(exc), "status": 401})
            return
        except HhApiError as exc:
            put_event({"type": "error", "sessionId": sid, "message": str(exc), "status": 502})
            return
        except Exception as exc:  # noqa: BLE001
            put_event(
                {
                    "type": "error",
                    "sessionId": sid,
                    "message": f"Синхронизация не удалась: {exc}",
                    "status": 500,
                }
            )
            return

        report = build_report(
            records,
            days=body.days,
            since=since,
            source="sync",
            incomplete=incomplete,
        )
        _store_report(sid, report)
        emit(on_progress, "done", done_msg)
        put_event({"type": "done", "sessionId": sid, "report": report, "message": done_msg})

    return StreamingResponse(
        _stream_job(worker),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/sync/cancel")
def cancel_sync(x_session_id: str | None = Header(default=None)) -> dict[str, str]:
    sid = (x_session_id or "").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="Нужен X-Session-Id")
    with _LOCK:
        event = _CANCEL.get(sid)
        if event is None:
            event = threading.Event()
            _CANCEL[sid] = event
        event.set()
    return {"status": "cancel_requested"}


async def _read_upload(file: UploadFile) -> bytes:
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if not raw:
        raise HTTPException(status_code=400, detail="Пустой файл")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Файл больше 15 МБ")
    return raw


def _report_from_upload(name: str, raw: bytes, on_progress: Any | None = None) -> dict[str, Any]:
    if name.endswith(".json"):
        if on_progress:
            emit(on_progress, "parse", "Читаю JSON-отчёт…")
        data = json.loads(raw.decode("utf-8"))
        if not _is_valid_report(data):
            raise ValueError("В JSON нет структуры отчёта дашборда (нужны поля meta и leads)")
        if on_progress:
            emit(on_progress, "build", "Подключаю готовый отчёт к дашборду…")
        return data

    if name.endswith(".xlsx"):
        if on_progress:
            emit(on_progress, "parse", "Читаю Excel-файл…")
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(raw)
            tmp_path = Path(tmp.name)
        try:
            records, days = records_from_excel(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
        if not records:
            raise ValueError(
                "В Excel не нашлось чатов. Нужна выгрузка из CLI (analyze_chats / python cli.py)."
            )
        if on_progress:
            emit(
                on_progress,
                "classify",
                f"Из файла собрано записей: {len(records)}",
                current=len(records),
                total=len(records),
            )
            emit(on_progress, "build", "Собираю отчёт для дашборда…")
        return build_report(records, days=days, source="upload")

    raise ValueError("Поддерживаются только файлы .xlsx и .json")


@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...),
    x_session_id: str | None = Header(default=None),
) -> dict[str, Any]:
    sid = _session_id(x_session_id, allow_client_mint=True)
    name = (file.filename or "").lower()
    raw = await _read_upload(file)
    try:
        report = _report_from_upload(name, raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Не удалось разобрать файл: {exc}") from exc

    _store_report(sid, report)
    return {"sessionId": sid, "report": report}


@app.post("/api/upload/stream")
async def upload_stream(
    file: UploadFile = File(...),
    x_session_id: str | None = Header(default=None),
) -> StreamingResponse:
    sid = _session_id(x_session_id, allow_client_mint=True)
    cancel = _cancel_event(sid)
    name = (file.filename or "upload").lower()
    raw = await _read_upload(file)
    filename = file.filename or name

    def worker(put_event: Any) -> None:
        def on_progress(event: ProgressEvent) -> None:
            put_event({"type": "progress", "sessionId": sid, **event})

        try:
            if cancel.is_set():
                put_event(
                    {
                        "type": "error",
                        "sessionId": sid,
                        "message": "Разбор файла остановили",
                        "status": 400,
                    }
                )
                return
            emit(on_progress, "start", f"Принял файл «{filename}»")
            emit(on_progress, "parse", "Читаю содержимое…")
            if cancel.is_set():
                put_event(
                    {
                        "type": "error",
                        "sessionId": sid,
                        "message": "Разбор файла остановили",
                        "status": 400,
                    }
                )
                return
            report = _report_from_upload(name, raw, on_progress=on_progress)
            _store_report(sid, report)
            emit(on_progress, "done", "Готово — отчёт открыт")
            put_event({"type": "done", "sessionId": sid, "report": report})
        except Exception as exc:  # noqa: BLE001
            put_event(
                {
                    "type": "error",
                    "sessionId": sid,
                    "message": f"Не удалось разобрать файл: {exc}",
                    "status": 400,
                }
            )

    return StreamingResponse(
        _stream_job(worker),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/report")
def get_report(x_session_id: str | None = Header(default=None)) -> dict[str, Any]:
    if not x_session_id:
        raise HTTPException(status_code=404, detail="Нет данных сессии. Сделайте sync или upload.")
    report = _get_report(x_session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Нет данных сессии. Сделайте sync или upload.")
    return {"sessionId": x_session_id, "report": report}


@app.get("/api/report/excel")
def get_report_excel(x_session_id: str | None = Header(default=None)) -> FileResponse:
    """Скачать текущий отчёт сессии как Excel."""
    if not x_session_id:
        raise HTTPException(status_code=404, detail="Нет данных сессии. Сначала загрузите чаты.")
    report = _get_report(x_session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Нет данных сессии. Сначала загрузите чаты.")

    records, days, since = records_from_report(report)
    if not records:
        raise HTTPException(status_code=400, detail="В отчёте нет чатов для выгрузки в Excel.")

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    write_excel(records, tmp_path, days, since)

    exported = str((report.get("meta") or {}).get("exportedAt") or "")
    stamp = re.sub(r"\D", "", exported)[:12] or datetime.now().strftime("%Y%m%d%H%M")
    filename = f"hh-leads-{stamp}.xlsx"

    return FileResponse(
        tmp_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
        background=BackgroundTask(lambda: tmp_path.unlink(missing_ok=True)),
    )


@app.delete("/api/session")
def clear_session(x_session_id: str | None = Header(default=None)) -> dict[str, str]:
    if x_session_id:
        with _LOCK:
            _SESSIONS.pop(x_session_id, None)
            event = _CANCEL.pop(x_session_id, None)
            if event:
                event.set()
    return {"status": "cleared"}


if WEB_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_DIST / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        safe = _safe_dist_file(full_path)
        if safe is not None:
            return FileResponse(safe)
        return FileResponse(WEB_DIST / "index.html")
