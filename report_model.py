"""JSON-модель отчёта для дашборда: лиды, теги, мета."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from classify import ChatRecord
from report_common import chat_id_from_url, fmt_dt


def lead_tag(rec: ChatRecord) -> str:
    """Выбирает одну плашку для UI.

    Сначала отказ, потом текущее ожидание или автоответ, затем «позвоните»,
    «нужен ответ», собес, тест и приглашение из истории.
    """
    if rec.vacancy_closed or rec.action == "Отказ / закрыто":
        return "closed"
    # Уже ответили — важнее старых категорий «приглашение» или «тестовое».
    if rec.action == "Ждать ответа HR":
        return "wait"
    if rec.action == "Автоответ / бот":
        return "bot"
    # Явная просьба позвонить или написать важнее простого «ответьте на сообщение».
    if rec.strong_contact:
        return "call"
    if rec.action == "Ответить работодателю":
        return "reply"
    if (
        rec.state_id.lower() == "interview"
        or rec.state_name == "Собеседование"
        or rec.action == "Собеседование / встреча"
    ):
        return "interview"
    if "Тестовые" in rec.categories or rec.action == "Тестовое задание":
        return "test"
    if "Приглашения" in rec.categories:
        return "invite"
    return "discuss"


def clean_why(text: str) -> str:
    """Убирает служебные префиксы классификатора из колонки «суть»."""
    why = re.sub(r"\s+", " ", text).strip()
    why = re.sub(
        r"^(?:последнее от HR|бот|последнее от тебя|автоответ)\s*[:·]\s*",
        "",
        why,
        flags=re.I,
    )
    return why[:160].rstrip(" ,.;:") or "—"


def record_to_lead(rec: ChatRecord) -> dict[str, Any]:
    why = rec.action_detail or "; ".join(rec.invite_reasons[:2] or rec.test_reasons[:2]) or rec.summary
    why = clean_why(why or "")
    return {
        "id": rec.negotiation_id or chat_id_from_url(rec.chat_url),
        "company": rec.company or "—",
        "vacancy": rec.vacancy_name or "—",
        "status": rec.state_name or rec.state_id or "—",
        "stateId": rec.state_id,
        "tag": lead_tag(rec),
        "action": rec.action,
        "why": why,
        "summary": rec.summary,
        "updated": fmt_dt(rec.updated_at),
        "chatUrl": rec.chat_url,
        "vacancyUrl": rec.vacancy_url,
        "closed": bool(rec.vacancy_closed or rec.action == "Отказ / закрыто"),
        "strong": bool(rec.strong_contact),
        "categories": list(rec.categories),
        "inviteReasons": list(rec.invite_reasons),
        "testReasons": list(rec.test_reasons),
        "lastFrom": rec.last_from,
    }


def category_counts(records: list[ChatRecord]) -> dict[str, int]:
    return {
        "invites": sum(1 for r in records if "Приглашения" in r.categories),
        "tests": sum(1 for r in records if "Тестовые" in r.categories),
        "discussions": sum(1 for r in records if "Обсуждения" in r.categories),
    }


def action_counts(records: list[ChatRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in records:
        counts[r.action] = counts.get(r.action, 0) + 1
    return counts


def build_report(
    records: list[ChatRecord],
    *,
    days: int,
    since: datetime | None = None,
    source: str = "sync",
    incomplete: bool = False,
) -> dict[str, Any]:
    counts = category_counts(records)
    action_counts_map = action_counts(records)

    state_counts: dict[str, int] = {}
    for r in records:
        key = r.state_name or r.state_id or "—"
        state_counts[key] = state_counts.get(key, 0) + 1

    leads = [record_to_lead(r) for r in records]
    reply = [l for l in leads if l["action"] == "Ответить работодателю"]
    interview_hh = [l for l in leads if l["tag"] == "interview" or l["status"] == "Собеседование"]
    contact = [l for l in leads if l["strong"]]
    tests = [l for l in leads if l["tag"] == "test" or "Тестовые" in (l.get("categories") or [])]
    invites = [l for l in leads if l["tag"] == "invite" or "Приглашения" in (l.get("categories") or [])]
    wait = [l for l in leads if l["tag"] == "wait"]
    bot = [l for l in leads if l["tag"] == "bot"]
    closed = [l for l in leads if l["tag"] == "closed" or l["closed"]]

    order = {
        "call": 0,
        "reply": 1,
        "interview": 2,
        "test": 3,
        "invite": 4,
        "wait": 5,
        "bot": 6,
        "discuss": 7,
        "closed": 8,
    }
    all_leads = sorted(
        leads,
        key=lambda x: (order.get(str(x.get("tag")), 9), x.get("updated") or ""),
    )

    period = f"Активность в чатах за последние {days} дн."
    period_from = None
    if since is not None:
        period_from = since.date().isoformat()
        period = f"Активность в чатах с {period_from}"
    if incomplete:
        period = f"{period} (загрузку остановили раньше времени)"

    exported_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")

    return {
        "meta": {
            "period": period,
            "periodFrom": period_from,
            "days": days,
            "exportedAt": exported_at,
            "source": source,
            "incomplete": incomplete,
            "total": len(records),
            "invites": counts["invites"],
            "tests": counts["tests"],
            "discussions": counts["discussions"],
            "multiCategory": sum(1 for r in records if len(r.categories) > 1),
            "actions": {
                "reply": action_counts_map.get("Ответить работодателю", 0),
                "interview": action_counts_map.get("Собеседование / встреча", 0),
                "test": action_counts_map.get("Тестовое задание", 0),
                "wait": action_counts_map.get("Ждать ответа HR", 0),
                "bot": action_counts_map.get("Автоответ / бот", 0),
                "closed": action_counts_map.get("Отказ / закрыто", 0),
            },
            "hhStatus": {
                "response": state_counts.get("Отклик", 0),
                "reject": state_counts.get("Отказ", 0),
                "interview": state_counts.get("Собеседование", 0),
            },
            "actionCounts": action_counts_map,
            "stateCounts": state_counts,
        },
        "leads": {
            "all": all_leads,
            "reply": reply,
            "interview": interview_hh,
            "contact": contact,
            "tests": tests,
            "invites": invites,
            "wait": wait,
            "bot": bot,
            "closed": closed,
        },
    }
