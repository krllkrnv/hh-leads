"""Тесты early-stop пагинации списка чатов."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

from hh_client import ChatikClient, SyncCancelled


def _chat(chat_id: str, hours_ago: float | None) -> dict[str, Any]:
    chat: dict[str, Any] = {"id": chat_id, "lastMessage": {}}
    if hours_ago is not None:
        ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        chat["lastActivityTime"] = ts.isoformat()
    return chat


def test_iter_chats_scans_full_page_before_stop() -> None:
    """На странице со смешанным порядком «молодые» после «старых» не теряются."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    client = ChatikClient.__new__(ChatikClient)
    pages = [
        {
            "chats": {
                "items": [
                    _chat("new1", 1),
                    _chat("old1", 24 * 30),
                    _chat("new2", 2),  # после old — всё равно в окне
                ],
                "pages": 1,
            },
            "chatsDisplayInfo": {},
            "resources": {},
        }
    ]
    client._get = MagicMock(side_effect=pages)  # type: ignore[method-assign]
    items = ChatikClient.iter_chats(client, since)
    ids = [e["chat"]["id"] for e in items]
    assert ids == ["new1", "new2"]


def test_iter_chats_skips_null_activity() -> None:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    client = ChatikClient.__new__(ChatikClient)
    client._get = MagicMock(  # type: ignore[method-assign]
        return_value={
            "chats": {
                "items": [_chat("no-ts", None), _chat("ok", 3)],
                "pages": 1,
            },
            "chatsDisplayInfo": {},
            "resources": {},
        }
    )
    items = ChatikClient.iter_chats(client, since)
    assert [e["chat"]["id"] for e in items] == ["ok"]


def test_iter_chats_cancel_raises() -> None:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    client = ChatikClient.__new__(ChatikClient)
    client._get = MagicMock()  # type: ignore[method-assign]
    try:
        ChatikClient.iter_chats(client, since, should_cancel=lambda: True)
        assert False, "expected SyncCancelled"
    except SyncCancelled:
        pass
    client._get.assert_not_called()
