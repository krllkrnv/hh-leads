"""Пайплайн: cookie → чаты → ChatRecord."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from classify import ChatRecord, classify, extract_messages, extract_meta
from hh_client import ChatikClient
from progress import ProgressCb, emit


def _company_label(entry: dict[str, Any]) -> str:
    display = entry.get("display") or {}
    chat = entry.get("chat") or {}
    for key in ("title", "name", "employerName", "companyName"):
        value = display.get(key) or chat.get(key)
        if value:
            return str(value)
    participants = display.get("participants") or chat.get("participants") or []
    if isinstance(participants, list):
        for person in participants:
            if not isinstance(person, dict):
                continue
            name = person.get("name") or person.get("displayName")
            if name:
                return str(name)
    return "чат"


def fetch_records(
    cookie: str,
    days: int,
    *,
    delay: float = 0.25,
    hh_host: str | None = None,
    on_progress: ProgressCb | None = None,
    should_cancel: Any | None = None,
) -> tuple[list[ChatRecord], datetime]:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    def cancelled() -> bool:
        return bool(callable(should_cancel) and should_cancel())

    emit(on_progress, "start", f"Старт синхронизации за последние {days} дн.")
    emit(on_progress, "auth", "Проверяю cookie и подключаюсь к Chatik…")

    with ChatikClient(cookie, delay=delay, hh_host=hh_host) as client:
        if cancelled():
            raise RuntimeError("Синхронизация отменена")

        applicant_id = client.get_applicant_id()
        if applicant_id:
            emit(on_progress, "auth", "Сессия принята, профиль найден")
        else:
            emit(
                on_progress,
                "warn",
                "Профиль не определён — разметка «я / HR» может быть грубее",
            )

        emit(on_progress, "list", "Собираю список чатов за период…")

        def on_page(page: int, collected: int) -> None:
            emit(
                on_progress,
                "list",
                f"Страница {page + 1}: уже {collected} чатов в выборке",
                current=collected,
            )

        chat_entries = client.iter_chats(since, on_page=on_page)
        total = len(chat_entries)
        emit(
            on_progress,
            "list",
            f"В окне {days} дн. найдено чатов: {total}",
            current=total,
            total=total,
        )

        records: list[ChatRecord] = []
        for idx, entry in enumerate(chat_entries, start=1):
            if cancelled():
                emit(
                    on_progress,
                    "warn",
                    f"Остановлено пользователем после {len(records)} чатов",
                    current=idx,
                    total=total,
                )
                raise RuntimeError("Синхронизация отменена")

            chat = entry["chat"]
            chat_id = str(chat.get("id") or "")
            company = _company_label(entry)
            emit(
                on_progress,
                "fetch",
                f"Читаю переписку: {company}",
                current=idx,
                total=total,
                company=company,
                detail=chat_id,
            )
            chat_data: dict[str, Any] = {}
            try:
                if chat_id:
                    chat_data = client.get_chat_data(chat_id)
            except Exception as exc:  # noqa: BLE001
                emit(
                    on_progress,
                    "warn",
                    f"Не удалось загрузить сообщения ({company}): {exc}",
                    current=idx,
                    total=total,
                    company=company,
                )
            messages = extract_messages(chat_data) if chat_data else []
            if not messages and chat.get("lastMessage"):
                lm = chat["lastMessage"]
                display = lm.get("participantDisplay") or {}
                participant_id = str(lm.get("participantId") or "")
                my_id = str((chat_data.get("chat") or {}).get("currentParticipantId") or "")
                if not my_id:
                    my_id = str(chat.get("currentParticipantId") or "")
                is_me = bool(my_id and participant_id == my_id)
                messages = [
                    {
                        "text": lm.get("text") or "",
                        "created_at": lm.get("creationTime"),
                        "author": display.get("name") or "",
                        "participant_id": participant_id,
                        "is_bot": bool(display.get("isBot")),
                        "is_me": is_me,
                        "workflow_state": None,
                    }
                ]
            emit(
                on_progress,
                "classify",
                f"Классифицирую: {company}",
                current=idx,
                total=total,
                company=company,
            )
            meta = extract_meta(
                chat,
                entry.get("display") or {},
                entry.get("list_resources") or {},
                chat_data,
                client=client,
            )
            records.append(classify(meta, messages))

    emit(on_progress, "build", f"Собираю отчёт по {len(records)} чатам…")
    return records, since
