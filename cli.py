"""CLI: анализ чатов hh.ru → Excel."""

from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from classify import ChatRecord
from hh_client import HhApiError, HhAuthError
from pipeline import fetch_records
from report import write_excel


def print_action_report(records: list[ChatRecord]) -> None:
    groups: dict[str, list[ChatRecord]] = {}
    for r in records:
        if r.action in (
            "Ответить работодателю",
            "Собеседование / встреча",
            "Тестовое задание",
        ):
            groups.setdefault(r.action, []).append(r)

    print("\n========== ЧТО СДЕЛАТЬ ==========")
    if not groups:
        print("Срочных действий (ответ / собес / тест) не найдено.")
        return

    for action in (
        "Ответить работодателю",
        "Собеседование / встреча",
        "Тестовое задание",
    ):
        items = groups.get(action) or []
        if not items:
            continue
        items.sort(
            key=lambda r: r.updated_at.timestamp() if r.updated_at else 0,
            reverse=True,
        )
        print(f"\n## {action} ({len(items)})")
        for r in items:
            company = r.company or "—"
            vac = r.vacancy_name or "—"
            print(f"- {company} · {vac}")
            if r.action_detail:
                print(f"  {r.action_detail}")
            if r.chat_url:
                print(f"  {r.chat_url}")
            if r.vacancy_url:
                print(f"  вакансия: {r.vacancy_url}")


def analyze(cookie: str, days: int, out_path: Path, delay: float, hh_host: str | None = None) -> Path:
    records, since = fetch_records(
        cookie,
        days,
        delay=delay,
        hh_host=hh_host,
        on_progress=lambda event: print(event.get("message", event), flush=True),
    )
    write_excel(records, out_path, days, since)
    print(f"Готово: {out_path}")
    print_action_report(records)
    return out_path


def main() -> None:
    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    load_dotenv()

    parser = argparse.ArgumentParser(description="Анализ чатов hh.ru → Excel (cookie)")
    parser.add_argument(
        "--days",
        type=int,
        default=60,
        help="Глубина по lastActivity, дни 1–180 (по умолчанию 60)",
    )
    parser.add_argument("--out", type=Path, help="Путь к .xlsx")
    parser.add_argument("--cookie", help="Cookie-строка (иначе HH_COOKIE)")
    parser.add_argument("--host", help="Базовый URL hh (по умолчанию https://hh.ru)")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.25,
        help="Пауза между запросами API, сек",
    )
    args = parser.parse_args()

    days = max(1, min(180, int(args.days)))
    if days != args.days:
        print(f"Внимание: --days обрезан до {days} (допустимо 1–180)", flush=True)

    cookie = (args.cookie or os.getenv("HH_COOKIE") or "").strip()
    if not cookie:
        raise SystemExit(
            "Не задан HH_COOKIE. Войдите на hh.ru, скопируйте Cookie из DevTools "
            "и положите в .env (см. README)."
        )

    out = args.out
    if out is None:
        today = date.today().isoformat()
        out = root / f"hh_chats_{days}d_{today}.xlsx"

    host = args.host or os.getenv("HH_HOST") or None
    try:
        analyze(cookie, days, out, args.delay, hh_host=host)
    except (HhAuthError, HhApiError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
