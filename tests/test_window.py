"""Тесты цепочки «дни → since → отчёт» и разбора дат."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from hh_leads import pipeline
from hh_leads.classify import extract_meta
from hh_leads.hh_client import ChatListResult, parse_dt
from hh_leads.jobs import build_sync_report, is_valid_report, run_fetch
from hh_leads.report import build_report


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class FakeClient:
    """Подменяет ChatikClient: запоминает since и отдаёт готовый список."""

    last_since: datetime | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.closed = False

    def __enter__(self) -> FakeClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.closed = True

    def get_applicant_id(self) -> str:
        return "42"

    def iter_chats(
        self,
        since: datetime,
        on_page: Any = None,
        should_cancel: Any = None,
        max_stale_pages: int = 5,
    ) -> ChatListResult:
        FakeClient.last_since = since
        newest = _now() - timedelta(hours=2)
        oldest = since + timedelta(hours=1)
        chat = {
            "id": "1",
            "lastMessage": {"creationTime": newest.isoformat(), "text": "привет"},
        }
        return ChatListResult(
            items=[{"chat": chat, "display": {}, "list_resources": {}}],
            scanned=137,
            pages_read=3,
            stopped_early=True,
            oldest=oldest,
            newest=newest,
        )

    def get_chat_data(self, chat_id: str) -> dict[str, Any]:
        return {}

    def chat_url(self, chat_id: str) -> str:
        return f"https://hh.ru/chat/{chat_id}"

    def vacancy_url(self, vacancy_id: str) -> str:
        return f"https://hh.ru/vacancy/{vacancy_id}"

    def topic_url(self, topic_id: str) -> str:
        return f"https://hh.ru/applicant/negotiations?topicId={topic_id}"


@pytest.fixture()
def fake_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "ChatikClient", FakeClient)


@pytest.mark.parametrize("days", [1, 7, 60, 180])
def test_days_reach_since(fake_client: None, days: int) -> None:
    """Число дней из формы доезжает до границы окна без подмен."""
    before = _now()
    records, since, stats = pipeline.fetch_records("hhtoken=x; _xsrf=y", days)
    expected = before - timedelta(days=days)
    assert abs((since - expected).total_seconds()) < 5
    assert len(records) == 1
    assert stats.scanned == 137


def test_report_window_is_verifiable(fake_client: None) -> None:
    """В meta лежит всё, чем можно проверить окно, не выгружая данные заново."""
    outcome = run_fetch(
        cookie="hhtoken=x; _xsrf=y",
        days=3,
        delay=0.0,
        hh_host=None,
        should_cancel=lambda: False,
    )
    report = build_sync_report(outcome, days=3)
    window = report["meta"]["window"]
    assert report["meta"]["days"] == 3
    assert window["field"] == "lastMessage.creationTime"
    assert window["scanned"] == 137
    assert window["kept"] == 1
    assert window["pagesRead"] == 3
    assert window["stoppedEarly"] is True
    assert window["oldest"] and window["newest"]
    assert is_valid_report(report)


def test_upload_report_has_no_window() -> None:
    """Отчёт из файла ничего не фильтровал, поэтому окна у него нет."""
    report = build_report([], days=60, source="upload")
    assert report["meta"]["window"] is None
    assert is_valid_report(report)


def test_extract_meta_uses_message_time() -> None:
    """Дата обновления лида берётся из сообщения, а не из lastActivityTime."""
    message_at = _now() - timedelta(days=10)
    touched_at = _now()
    chat = {
        "id": "77",
        "lastActivityTime": touched_at.isoformat(),
        "lastMessage": {"creationTime": message_at.isoformat()},
    }
    meta = extract_meta(chat, {}, {}, {})
    assert meta["updated_at"] is not None
    assert abs((meta["updated_at"] - message_at).total_seconds()) < 2


@pytest.mark.parametrize(
    "raw",
    [
        "2026-08-11T18:00:00Z",
        "2026-08-11T18:00:00+0000",
        "2026-08-11T18:00:00+00:00",
        "2026-08-11T18:00:00",
        1786557600,
        1786557600000,
    ],
)
def test_parse_dt_formats(raw: Any) -> None:
    parsed = parse_dt(raw)
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.astimezone(timezone.utc).year == 2026


def test_parse_dt_rejects_junk() -> None:
    assert parse_dt(None) is None
    assert parse_dt("") is None
    assert parse_dt("вчера") is None
