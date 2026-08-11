"""Тесты пагинации списка чатов без early-stop по возрасту."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

from hh_leads.hh_client import ChatikClient, SyncCancelled


def _chat(chat_id: str, hours_ago: float | None) -> dict[str, Any]:
    chat: dict[str, Any] = {"id": chat_id, "lastMessage": {}}
    if hours_ago is not None:
        ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        chat["lastActivityTime"] = ts.isoformat()
    return chat


def test_iter_chats_keeps_young_after_old_on_same_page() -> None:
    """На странице со смешанным порядком «молодые» после «старых» не теряются."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    client = ChatikClient.__new__(ChatikClient)
    pages = [
        {
            "chats": {
                "items": [
                    _chat("new1", 1),
                    _chat("old1", 24 * 30),
                    _chat("new2", 2),
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


def test_iter_chats_continues_after_old_chat_on_earlier_page() -> None:
    """Старый чат на ранней странице не обрывает пагинацию: следующие страницы читаем."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    client = ChatikClient.__new__(ChatikClient)
    pages = [
        {
            "chats": {
                "items": [
                    _chat("new1", 1),
                    _chat("old1", 24 * 30),
                ],
                "pages": 2,
            },
            "chatsDisplayInfo": {},
            "resources": {},
        },
        {
            "chats": {
                "items": [
                    _chat("new2", 3),
                    _chat("old2", 24 * 40),
                ],
                "pages": 2,
            },
            "chatsDisplayInfo": {},
            "resources": {},
        },
    ]
    client._get = MagicMock(side_effect=pages)  # type: ignore[method-assign]
    items = ChatikClient.iter_chats(client, since)
    ids = [e["chat"]["id"] for e in items]
    assert ids == ["new1", "new2"]
    assert client._get.call_count == 2


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
