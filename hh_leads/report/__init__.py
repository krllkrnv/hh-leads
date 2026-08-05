"""Отчёт для UI/Excel: публичный фасад над моделью, экспортом и импортом."""

from __future__ import annotations

from hh_leads.report.excel_export import (
    ACTION_COLUMNS,
    COLUMNS,
    action_row,
    autosize,
    record_row,
    write_excel,
)
from hh_leads.report.excel_import import records_from_excel
from hh_leads.report.common import STATE_ID_BY_NAME, chat_id_from_url, fmt_dt, parse_excel_dt
from hh_leads.report.model import build_report, clean_why, lead_tag, record_to_lead
from hh_leads.report.roundtrip import records_from_report

__all__ = [
    "ACTION_COLUMNS",
    "COLUMNS",
    "STATE_ID_BY_NAME",
    "action_row",
    "autosize",
    "build_report",
    "chat_id_from_url",
    "clean_why",
    "fmt_dt",
    "lead_tag",
    "parse_excel_dt",
    "record_row",
    "record_to_lead",
    "records_from_excel",
    "records_from_report",
    "write_excel",
]
