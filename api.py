"""FastAPI: sync / upload / report / clear session для локального дашборда."""

from __future__ import annotations

import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from jobs import (
    build_sync_report,
    check_upload_cancel,
    is_valid_report as _is_valid_report,
    map_sync_http_error,
    report_from_upload,
    run_fetch,
)
from progress import ProgressEvent, emit
from report import records_from_report, write_excel
from session_store import (
    cancel_event,
    clear_session as store_clear_session,
    get_report,
    request_cancel,
    session_id,
    store_report,
)
from streaming import stream_job

ROOT = Path(__file__).resolve().parent
WEB_DIST = ROOT / "web" / "dist"
WEB_DIST_RESOLVED = WEB_DIST.resolve()

MAX_UPLOAD_BYTES = 15 * 1024 * 1024

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
    sid = session_id(x_session_id, allow_client_mint=True)
    cancel = cancel_event(sid)
    try:
        outcome = run_fetch(
            cookie=body.cookie,
            days=body.days,
            delay=body.delay,
            hh_host=body.hhHost,
            should_cancel=cancel.is_set,
        )
    except Exception as exc:  # noqa: BLE001
        status, detail = map_sync_http_error(exc)
        raise HTTPException(status_code=status, detail=detail) from exc

    report = build_sync_report(outcome, days=body.days)
    store_report(sid, report)
    return {"sessionId": sid, "report": report}


@app.post("/api/sync/stream")
def sync_stream(
    body: SyncBody,
    x_session_id: str | None = Header(default=None),
) -> StreamingResponse:
    sid = session_id(x_session_id, allow_client_mint=True)
    cancel = cancel_event(sid)

    def worker(put_event: Any) -> None:
        def on_progress(event: ProgressEvent) -> None:
            put_event({"type": "progress", "sessionId": sid, **event})

        try:
            outcome = run_fetch(
                cookie=body.cookie,
                days=body.days,
                delay=body.delay,
                hh_host=body.hhHost,
                should_cancel=cancel.is_set,
                on_progress=on_progress,
            )
        except Exception as exc:  # noqa: BLE001
            status, message = map_sync_http_error(exc)
            put_event({"type": "error", "sessionId": sid, "message": message, "status": status})
            return

        report = build_sync_report(outcome, days=body.days)
        store_report(sid, report)
        emit(on_progress, "done", outcome.done_msg)
        put_event({"type": "done", "sessionId": sid, "report": report, "message": outcome.done_msg})

    return StreamingResponse(
        stream_job(worker),
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
    request_cancel(sid)
    return {"status": "cancel_requested"}


async def _read_upload(file: UploadFile) -> bytes:
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if not raw:
        raise HTTPException(status_code=400, detail="Пустой файл")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Файл больше 15 МБ")
    return raw


@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...),
    x_session_id: str | None = Header(default=None),
) -> dict[str, Any]:
    sid = session_id(x_session_id, allow_client_mint=True)
    name = (file.filename or "").lower()
    raw = await _read_upload(file)
    try:
        report = report_from_upload(name, raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Не удалось разобрать файл: {exc}") from exc

    store_report(sid, report)
    return {"sessionId": sid, "report": report}


@app.post("/api/upload/stream")
async def upload_stream(
    file: UploadFile = File(...),
    x_session_id: str | None = Header(default=None),
) -> StreamingResponse:
    sid = session_id(x_session_id, allow_client_mint=True)
    cancel = cancel_event(sid)
    name = (file.filename or "upload").lower()
    raw = await _read_upload(file)
    filename = file.filename or name

    def worker(put_event: Any) -> None:
        def on_progress(event: ProgressEvent) -> None:
            put_event({"type": "progress", "sessionId": sid, **event})

        try:
            if check_upload_cancel(cancel, sid, put_event):
                return
            emit(on_progress, "start", f"Принял файл «{filename}»")
            emit(on_progress, "parse", "Читаю содержимое…")
            if check_upload_cancel(cancel, sid, put_event):
                return
            report = report_from_upload(name, raw, on_progress=on_progress)
            store_report(sid, report)
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
        stream_job(worker),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/report")
def get_report_route(x_session_id: str | None = Header(default=None)) -> dict[str, Any]:
    if not x_session_id:
        raise HTTPException(status_code=404, detail="Нет данных сессии. Сделайте sync или upload.")
    report = get_report(x_session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Нет данных сессии. Сделайте sync или upload.")
    return {"sessionId": x_session_id, "report": report}


@app.get("/api/report/excel")
def get_report_excel(x_session_id: str | None = Header(default=None)) -> FileResponse:
    """Скачать текущий отчёт сессии как Excel."""
    if not x_session_id:
        raise HTTPException(status_code=404, detail="Нет данных сессии. Сначала загрузите чаты.")
    report = get_report(x_session_id)
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
def clear_session_route(x_session_id: str | None = Header(default=None)) -> dict[str, str]:
    if x_session_id:
        store_clear_session(x_session_id)
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
