"""In-memory сессии отчётов для локального дашборда."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any

MAX_SESSIONS = 32
SESSION_TTL_SEC = 6 * 60 * 60


@dataclass
class SessionEntry:
    report: dict[str, Any]
    touched_at: float = field(default_factory=time.time)


_SESSIONS: dict[str, SessionEntry] = {}
_CANCEL: dict[str, threading.Event] = {}
_LOCK = threading.Lock()


def prune_sessions() -> None:
    now = time.time()
    expired = [sid for sid, entry in _SESSIONS.items() if now - entry.touched_at > SESSION_TTL_SEC]
    for sid in expired:
        _SESSIONS.pop(sid, None)
        _CANCEL.pop(sid, None)
    while len(_SESSIONS) > MAX_SESSIONS:
        oldest = min(_SESSIONS.items(), key=lambda item: item[1].touched_at)[0]
        _SESSIONS.pop(oldest, None)
        _CANCEL.pop(oldest, None)


def store_report(sid: str, report: dict[str, Any]) -> None:
    with _LOCK:
        prune_sessions()
        _SESSIONS[sid] = SessionEntry(report=report)
        _CANCEL.pop(sid, None)


def get_report(sid: str) -> dict[str, Any] | None:
    with _LOCK:
        entry = _SESSIONS.get(sid)
        if not entry:
            return None
        if time.time() - entry.touched_at > SESSION_TTL_SEC:
            _SESSIONS.pop(sid, None)
            return None
        entry.touched_at = time.time()
        return entry.report


def session_id(x_session_id: str | None, *, allow_client_mint: bool = False) -> str:
    """Переиспользует известный id; для sync/upload может принять клиентский id для cancel."""
    candidate = (x_session_id or "").strip()
    with _LOCK:
        prune_sessions()
        if candidate and candidate in _SESSIONS:
            return candidate
        if allow_client_mint and candidate and 16 <= len(candidate) <= 80:
            return candidate
    return secrets.token_urlsafe(16)


def cancel_event(sid: str) -> threading.Event:
    with _LOCK:
        event = _CANCEL.get(sid)
        if event is None:
            event = threading.Event()
            _CANCEL[sid] = event
        else:
            event.clear()
        return event


def request_cancel(sid: str) -> None:
    with _LOCK:
        event = _CANCEL.get(sid)
        if event is None:
            event = threading.Event()
            _CANCEL[sid] = event
        event.set()


def clear_session(sid: str) -> None:
    with _LOCK:
        _SESSIONS.pop(sid, None)
        event = _CANCEL.pop(sid, None)
        if event:
            event.set()
