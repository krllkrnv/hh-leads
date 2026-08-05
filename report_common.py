"""Общие хелперы для сборки отчёта и Excel."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

STATE_ID_BY_NAME = {
    "Отклик": "response",
    "Приглашение": "invitation",
    "Собеседование": "interview",
    "Отказ": "discard",
    "Выход на работу": "hired",
    "Скрытый": "hidden",
}


def fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.astimezone().strftime("%Y-%m-%d %H:%M")


def parse_excel_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def chat_id_from_url(url: str) -> str:
    m = re.search(r"/chat/(\d+)", str(url or ""))
    return m.group(1) if m else ""
