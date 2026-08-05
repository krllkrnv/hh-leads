"""Smoke-тесты бакетов отчёта и path-safety."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from hh_leads.api import _is_valid_report, _safe_dist_file
from hh_leads.classify import ChatRecord
from hh_leads.report import build_report, lead_tag


def _rec(**kwargs: object) -> ChatRecord:
    base = dict(
        negotiation_id="1",
        company="Acme",
        vacancy_name="Frontend",
        vacancy_url="",
        chat_url="https://hh.ru/chat/1",
        state_id="response",
        state_name="Отклик",
        updated_at=datetime.now(timezone.utc),
        first_message_at=None,
        summary="",
        categories=["Обсуждения"],
        invite_reasons=[],
        test_reasons=[],
        strong_contact=False,
        vacancy_closed=False,
        action="Ждать ответа HR",
        action_detail="ждём",
        last_from="я",
    )
    base.update(kwargs)
    return ChatRecord(**base)  # type: ignore[arg-type]


def test_lead_tag_wait_not_invite() -> None:
    assert lead_tag(_rec()) == "wait"
    assert lead_tag(_rec(action="Автоответ / бот")) == "bot"
    assert lead_tag(_rec(action="Без действия", categories=["Обсуждения"])) == "discuss"


def test_build_report_all_includes_wait() -> None:
    records = [
        _rec(negotiation_id="w1", action="Ждать ответа HR"),
        _rec(
            negotiation_id="r1",
            action="Ответить работодателю",
            action_detail="вопрос",
            last_from="работодатель",
        ),
        _rec(
            negotiation_id="c1",
            action="Отказ / закрыто",
            vacancy_closed=True,
            categories=["Обсуждения"],
        ),
    ]
    report = build_report(records, days=30, source="sync")
    assert report["meta"]["total"] == 3
    assert len(report["leads"]["all"]) == 3
    assert len(report["leads"]["wait"]) == 1
    assert len(report["leads"]["closed"]) == 1
    assert len(report["leads"]["reply"]) == 1


def test_safe_dist_blocks_traversal(tmp_path: Path, monkeypatch: object) -> None:
    # Function uses module WEB_DIST; skip if dist missing — just assert helper rejects ..
    from hh_leads.api import WEB_DIST_RESOLVED

    assert WEB_DIST_RESOLVED.name == "dist"
    # Path outside dist must be None
    assert _safe_dist_file("../../.env") is None
    assert _safe_dist_file("../api.py") is None


def test_valid_report_schema() -> None:
    assert not _is_valid_report({"meta": {}, "leads": {}})
    assert _is_valid_report(
        {
            "meta": {"total": 0},
            "leads": {
                "all": [],
                "reply": [],
                "interview": [],
                "contact": [],
                "tests": [],
                "invites": [],
                "closed": [],
            },
        }
    )
