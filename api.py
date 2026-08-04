"""FastAPI: sync / upload / report / clear session для локального дашборда."""

from __future__ import annotations

import json
import secrets
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from hh_client import HhApiError, HhAuthError
from pipeline import fetch_records
from report import build_report, records_from_excel

ROOT = Path(__file__).resolve().parent
WEB_DIST = ROOT / "web" / "dist"

# session_id -> report dict (in-memory, single-user local tool)
_SESSIONS: dict[str, dict[str, Any]] = {}

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


def _session_id(x_session_id: str | None) -> str:
    if x_session_id and x_session_id.strip():
        return x_session_id.strip()
    return secrets.token_urlsafe(16)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sync")
def sync(body: SyncBody, x_session_id: str | None = Header(default=None)) -> dict[str, Any]:
    sid = _session_id(x_session_id)
    try:
        records, since = fetch_records(
            body.cookie,
            body.days,
            delay=body.delay,
            hh_host=body.hhHost,
        )
    except HhAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except HhApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Sync failed: {exc}") from exc

    report = build_report(records, days=body.days, since=since, source="sync")
    _SESSIONS[sid] = report
    return {"sessionId": sid, "report": report}


@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...),
    x_session_id: str | None = Header(default=None),
) -> dict[str, Any]:
    sid = _session_id(x_session_id)
    name = (file.filename or "").lower()
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Пустой файл")

    try:
        if name.endswith(".json"):
            data = json.loads(raw.decode("utf-8"))
            if isinstance(data, dict) and "meta" in data and "leads" in data:
                report = data
            else:
                raise HTTPException(
                    status_code=400,
                    detail="JSON должен быть отчётом дашборда (meta + leads)",
                )
        elif name.endswith(".xlsx"):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(raw)
                tmp_path = Path(tmp.name)
            try:
                records, days = records_from_excel(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
            if not records:
                raise HTTPException(
                    status_code=400,
                    detail="В Excel не найдено чатов. Нужна выгрузка analyze_chats / CLI.",
                )
            report = build_report(records, days=days, source="upload")
        else:
            raise HTTPException(status_code=400, detail="Поддерживаются .xlsx и .json")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Не удалось разобрать файл: {exc}") from exc

    _SESSIONS[sid] = report
    return {"sessionId": sid, "report": report}


@app.get("/api/report")
def get_report(x_session_id: str | None = Header(default=None)) -> dict[str, Any]:
    if not x_session_id or x_session_id not in _SESSIONS:
        raise HTTPException(status_code=404, detail="Нет данных сессии. Сделайте sync или upload.")
    return {"sessionId": x_session_id, "report": _SESSIONS[x_session_id]}


@app.delete("/api/session")
def clear_session(x_session_id: str | None = Header(default=None)) -> dict[str, str]:
    if x_session_id and x_session_id in _SESSIONS:
        del _SESSIONS[x_session_id]
    return {"status": "cleared"}


if WEB_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_DIST / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        candidate = WEB_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")
