"""Сборка ChatRecord из JSON-отчёта дашборда (для выгрузки в Excel)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from classify import ChatRecord
from report_common import STATE_ID_BY_NAME, chat_id_from_url, parse_excel_dt


def records_from_report(report: dict[str, Any]) -> tuple[list[ChatRecord], int, datetime]:
    """Собирает ChatRecord из JSON-отчёта дашборда для выгрузки в Excel."""
    meta = report.get("meta") if isinstance(report.get("meta"), dict) else {}
    try:
        days = max(1, min(180, int(meta.get("days") or 60)))
    except (TypeError, ValueError):
        days = 60

    period_from = meta.get("periodFrom")
    since: datetime | None = None
    if period_from:
        try:
            since = datetime.fromisoformat(str(period_from))
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
        except ValueError:
            since = None
    if since is None:
        since = datetime.now(timezone.utc) - timedelta(days=days)

    leads = report.get("leads") if isinstance(report.get("leads"), dict) else {}
    items = leads.get("all") if isinstance(leads.get("all"), list) else []
    records: list[ChatRecord] = []
    for lead in items:
        if not isinstance(lead, dict):
            continue
        chat_url = str(lead.get("chatUrl") or "")
        cid = str(lead.get("id") or "") or chat_id_from_url(chat_url)
        status_name = str(lead.get("status") or "")
        state_id = str(lead.get("stateId") or STATE_ID_BY_NAME.get(status_name, "") or "")
        categories = lead.get("categories")
        if not isinstance(categories, list) or not categories:
            categories = ["Обсуждения"]
        invite_reasons = lead.get("inviteReasons")
        if not isinstance(invite_reasons, list):
            invite_reasons = []
        test_reasons = lead.get("testReasons")
        if not isinstance(test_reasons, list):
            test_reasons = []
        records.append(
            ChatRecord(
                negotiation_id=cid,
                company=str(lead.get("company") or ""),
                vacancy_name=str(lead.get("vacancy") or ""),
                vacancy_url=str(lead.get("vacancyUrl") or ""),
                chat_url=chat_url,
                state_id=state_id,
                state_name=status_name,
                updated_at=parse_excel_dt(lead.get("updated")),
                first_message_at=None,
                summary=str(lead.get("summary") or lead.get("why") or ""),
                invite_reasons=[str(x) for x in invite_reasons],
                test_reasons=[str(x) for x in test_reasons],
                categories=[str(c) for c in categories],
                action=str(lead.get("action") or "Без действия"),
                action_detail=str(lead.get("why") or ""),
                last_from=str(lead.get("lastFrom") or ""),
                strong_contact=bool(lead.get("strong")),
                vacancy_closed=bool(lead.get("closed")),
            )
        )
    return records, days, since
