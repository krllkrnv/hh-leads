"""Тесты окна в днях и пагинации списка чатов."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest

from hh_leads.hh_client import ChatikClient, SyncCancelled, chat_activity_at


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _iso(hours_ago: float) -> str:
    return (_now() - timedelta(hours=hours_ago)).isoformat()


def _chat(chat_id: str, hours_ago: float | None, activity_hours_ago: float | None = None) -> dict[str, Any]:
    """Чат со временем последнего сообщения и, отдельно, с lastActivityTime."""
    chat: dict[str, Any] = {"id": chat_id, "lastMessage": {}}
    if hours_ago is not None:
        chat["lastMessage"] = {"creationTime": _iso(hours_ago)}
    if activity_hours_ago is not None:
        chat["lastActivityTime"] = _iso(activity_hours_ago)
    return chat


def _page(items: list[dict[str, Any]], pages: int) -> dict[str, Any]:
    return {
        "chats": {"items": items, "pages": pages},
        "chatsDisplayInfo": {},
        "resources": {},
    }


def _client(pages: list[dict[str, Any]]) -> ChatikClient:
    client = ChatikClient.__new__(ChatikClient)
    client._get = MagicMock(side_effect=pages)  # type: ignore[method-assign]
    return client


def test_window_ignores_touched_last_activity_time() -> None:
    """Свежий lastActivityTime без нового сообщения в окно не тянет.

    Chatik двигает lastActivityTime и когда переписка не менялась, поэтому
    чат со старым сообщением обязан выпасть из окна в один день.
    """
    since = _now() - timedelta(days=1)
    client = _client([_page([_chat("stale", hours_ago=24 * 30, activity_hours_ago=0.1)], pages=1)])
    result = ChatikClient.iter_chats(client, since)
    assert result.items == []
    assert result.scanned == 1


def test_window_size_changes_result() -> None:
    """Один и тот же список при окне в 1 и 60 дней даёт разные выборки.

    Все чаты помечены свежим lastActivityTime, как будто их только что читал
    сам дашборд. Раньше из-за этого любое окно возвращало одинаковый список.
    """
    page = _page(
        [
            _chat("hours", hours_ago=2, activity_hours_ago=0.1),
            _chat("days5", hours_ago=24 * 5, activity_hours_ago=0.1),
            _chat("days30", hours_ago=24 * 30, activity_hours_ago=0.1),
            _chat("days100", hours_ago=24 * 100, activity_hours_ago=0.1),
        ],
        pages=1,
    )

    day = ChatikClient.iter_chats(_client([page]), _now() - timedelta(days=1))
    two_months = ChatikClient.iter_chats(_client([page]), _now() - timedelta(days=60))

    assert [e["chat"]["id"] for e in day.items] == ["hours"]
    assert [e["chat"]["id"] for e in two_months.items] == ["hours", "days5", "days30"]


def test_window_falls_back_to_last_activity_without_message() -> None:
    """Если сообщения в элементе списка нет, берём lastActivityTime."""
    since = _now() - timedelta(days=7)
    client = _client([_page([_chat("only-activity", hours_ago=None, activity_hours_ago=2)], pages=1)])
    result = ChatikClient.iter_chats(client, since)
    assert [e["chat"]["id"] for e in result.items] == ["only-activity"]


def test_iter_chats_keeps_young_after_old_on_same_page() -> None:
    """На странице со смешанным порядком «молодые» после «старых» не теряются."""
    since = _now() - timedelta(days=7)
    client = _client(
        [_page([_chat("new1", 1), _chat("old1", 24 * 30), _chat("new2", 2)], pages=1)]
    )
    result = ChatikClient.iter_chats(client, since)
    assert [e["chat"]["id"] for e in result.items] == ["new1", "new2"]


def test_iter_chats_continues_after_old_chat_on_earlier_page() -> None:
    """Старый чат на ранней странице не обрывает пагинацию: следующие страницы читаем."""
    since = _now() - timedelta(days=7)
    client = _client(
        [
            _page([_chat("new1", 1), _chat("old1", 24 * 30)], pages=2),
            _page([_chat("new2", 3), _chat("old2", 24 * 40)], pages=2),
        ]
    )
    result = ChatikClient.iter_chats(client, since)
    assert [e["chat"]["id"] for e in result.items] == ["new1", "new2"]
    assert client._get.call_count == 2
    assert result.stopped_early is False


def test_iter_chats_stops_after_stale_pages() -> None:
    """Подряд идущие страницы без единого чата в окне обрывают обход."""
    since = _now() - timedelta(days=7)
    pages = [_page([_chat("new1", 1)], pages=99)] + [
        _page([_chat(f"old{i}", 24 * 90)], pages=99) for i in range(10)
    ]
    client = _client(pages)
    result = ChatikClient.iter_chats(client, since, max_stale_pages=2)
    assert [e["chat"]["id"] for e in result.items] == ["new1"]
    assert result.stopped_early is True
    assert client._get.call_count == 3


def test_iter_chats_reads_all_pages_when_stale_limit_disabled() -> None:
    since = _now() - timedelta(days=7)
    pages = [_page([_chat(f"old{i}", 24 * 90)], pages=4) for i in range(4)]
    client = _client(pages)
    result = ChatikClient.iter_chats(client, since, max_stale_pages=0)
    assert client._get.call_count == 4
    assert result.stopped_early is False
    assert result.scanned == 4
    assert result.items == []


def test_iter_chats_collects_window_stats() -> None:
    since = _now() - timedelta(days=7)
    client = _client([_page([_chat("a", 1), _chat("b", 100), _chat("c", 24 * 30)], pages=1)])
    result = ChatikClient.iter_chats(client, since)
    assert result.scanned == 3
    assert len(result.items) == 2
    assert result.pages_read == 1
    assert result.newest is not None and result.oldest is not None
    assert result.newest > result.oldest
    assert result.oldest >= since


def test_iter_chats_skips_null_activity() -> None:
    since = _now() - timedelta(days=7)
    client = _client([_page([_chat("no-ts", None), _chat("ok", 3)], pages=1)])
    result = ChatikClient.iter_chats(client, since)
    assert [e["chat"]["id"] for e in result.items] == ["ok"]


def test_iter_chats_cancel_raises() -> None:
    since = _now() - timedelta(days=7)
    client = ChatikClient.__new__(ChatikClient)
    client._get = MagicMock()  # type: ignore[method-assign]
    with pytest.raises(SyncCancelled):
        ChatikClient.iter_chats(client, since, should_cancel=lambda: True)
    client._get.assert_not_called()


def test_chat_activity_prefers_message_time() -> None:
    chat = _chat("x", hours_ago=50, activity_hours_ago=1)
    activity = chat_activity_at(chat)
    assert activity is not None
    age_hours = (_now() - activity).total_seconds() / 3600
    assert 49 < age_hours < 51
