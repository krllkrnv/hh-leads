"""Общая логика sync/upload для обычных и streaming-роутов."""

from __future__ import annotations

import json
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from hh_leads.classify import ChatRecord
from hh_leads.hh_client import HhApiError, HhAuthError
from hh_leads.pipeline import PartialSync, SyncStats, fetch_records
from hh_leads.progress import ProgressEvent, emit
from hh_leads.report import build_report, records_from_excel


@dataclass
class SyncOutcome:
    records: list[ChatRecord]
    since: datetime
    incomplete: bool
    done_msg: str
    stats: SyncStats


def is_valid_report(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    meta = data.get("meta")
    leads = data.get("leads")
    if not isinstance(meta, dict) or not isinstance(leads, dict):
        return False
    required_lead_keys = ("all", "reply", "interview", "contact", "tests", "invites", "closed")
    return all(key in leads and isinstance(leads[key], list) for key in required_lead_keys)


def run_fetch(
    *,
    cookie: str,
    days: int,
    delay: float,
    hh_host: str | None,
    should_cancel: Callable[[], bool],
    on_progress: Callable[[ProgressEvent], None] | None = None,
) -> SyncOutcome:
    """Тянет чаты и классифицирует. PartialSync → incomplete=True, не исключение."""
    try:
        records, since, stats = fetch_records(
            cookie,
            days,
            delay=delay,
            hh_host=hh_host,
            on_progress=on_progress,
            should_cancel=should_cancel,
        )
        return SyncOutcome(
            records=records,
            since=since,
            incomplete=False,
            done_msg="Готово — отчёт собран",
            stats=stats,
        )
    except PartialSync as partial:
        records, since = partial.records, partial.since
        done_msg = (
            f"Остановили раньше времени: в отчёте {len(records)} уже разобранных чатов"
            if records
            else "Остановили до того, как успели разобрать хотя бы один чат"
        )
        if on_progress:
            emit(on_progress, "warn", done_msg)
        return SyncOutcome(
            records=records,
            since=since,
            incomplete=True,
            done_msg=done_msg,
            stats=partial.stats,
        )


def build_sync_report(
    outcome: SyncOutcome,
    *,
    days: int,
) -> dict[str, Any]:
    return build_report(
        outcome.records,
        days=days,
        since=outcome.since,
        source="sync",
        incomplete=outcome.incomplete,
        stats=outcome.stats,
    )


def report_from_upload(
    name: str,
    raw: bytes,
    on_progress: Callable[[ProgressEvent], None] | None = None,
) -> dict[str, Any]:
    if name.endswith(".json"):
        if on_progress:
            emit(on_progress, "parse", "Читаю JSON-отчёт…")
        data = json.loads(raw.decode("utf-8"))
        if not is_valid_report(data):
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
                "В Excel не нашлось чатов. Нужна выгрузка из этого дашборда (JSON или Excel)."
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


def map_sync_http_error(exc: BaseException) -> tuple[int, str]:
    if isinstance(exc, HhAuthError):
        return 401, str(exc)
    if isinstance(exc, HhApiError):
        return 502, str(exc)
    return 500, f"Синхронизация не удалась: {exc}"


def upload_cancelled_payload(sid: str) -> dict[str, Any]:
    return {
        "type": "error",
        "sessionId": sid,
        "message": "Разбор файла остановили",
        "status": 400,
    }


def check_upload_cancel(
    cancel: threading.Event,
    sid: str,
    put_event: Callable[[dict[str, Any]], None],
) -> bool:
    """Если отмена запрошена — пишет error-событие и возвращает True."""
    if cancel.is_set():
        put_event(upload_cancelled_payload(sid))
        return True
    return False
