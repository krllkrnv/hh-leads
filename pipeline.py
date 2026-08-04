"""Пайплайн: cookie → чаты → ChatRecord."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from classify import ChatRecord, classify, extract_messages, extract_meta
from hh_client import ChatikClient


ProgressCb = Callable[[str], None]


def fetch_records(
    cookie: str,
    days: int,
    *,
    delay: float = 0.25,
    hh_host: str | None = None,
    on_progress: ProgressCb | None = None,
) -> tuple[list[ChatRecord], datetime]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    log = on_progress or (lambda _msg: None)

    log(f"Загружаю чаты с {since.isoformat()} …")
    with ChatikClient(cookie, delay=delay, hh_host=hh_host) as client:
        applicant_id = client.get_applicant_id()
        if applicant_id:
            log(f"applicantId: {applicant_id}")
        else:
            log("applicantId не определён — определение «я/HR» может быть неточным")

        chat_entries = client.iter_chats(since)
        log(f"Найдено чатов в окне: {len(chat_entries)}")
        records: list[ChatRecord] = []
        for idx, entry in enumerate(chat_entries, start=1):
            chat = entry["chat"]
            chat_id = str(chat.get("id") or "")
            log(f"[{idx}/{len(chat_entries)}] сообщения для {chat_id} …")
            chat_data: dict[str, Any] = {}
            try:
                if chat_id:
                    chat_data = client.get_chat_data(chat_id)
            except Exception as exc:  # noqa: BLE001
                log(f"  предупреждение: не удалось загрузить сообщения: {exc}")
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
            meta = extract_meta(
                chat,
                entry.get("display") or {},
                entry.get("list_resources") or {},
                chat_data,
                client=client,
            )
            records.append(classify(meta, messages))
    return records, since
