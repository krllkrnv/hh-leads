"""HTTP-клиент Chatik API (hh.ru applicant chats)."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import unquote

import httpx

CHATIK_BASE = "https://chatik.hh.ru"
DEFAULT_HH_HOST = "https://hh.ru"
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class HhAuthError(Exception):
    """Недействительная или неполная cookie-сессия."""


class HhApiError(Exception):
    """Ошибка ответа Chatik API."""


def normalize_cookie(raw: str) -> str:
    text = raw.strip()
    if text.lower().startswith("cookie:"):
        text = text.split(":", 1)[1].strip()
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        text = text[1:-1]
    return text.strip()


def cookie_value(cookie: str, name: str) -> str:
    for part in cookie.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, val = part.split("=", 1)
        if key.strip() == name:
            return unquote(val.strip())
    return ""


def parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    text = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", text)
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def normalize_hh_host(host: str | None) -> str:
    value = (host or DEFAULT_HH_HOST).strip().rstrip("/")
    if not value.startswith("http"):
        value = f"https://{value}"
    return value


class ChatikClient:
    def __init__(
        self,
        cookie: str,
        *,
        user_agent: str = DEFAULT_UA,
        delay: float = 0.25,
        hh_host: str | None = None,
    ) -> None:
        self.cookie = normalize_cookie(cookie)
        self.delay = delay
        self.hh_host = normalize_hh_host(hh_host)
        self.xsrf = cookie_value(self.cookie, "_xsrf")
        if not cookie_value(self.cookie, "hhtoken"):
            raise HhAuthError("В cookie нет hhtoken. Скопируйте Cookie после входа на hh.ru.")
        if not self.xsrf:
            raise HhAuthError("В cookie нет _xsrf. Скопируйте Cookie после входа на hh.ru.")

        self._client = httpx.Client(
            base_url=CHATIK_BASE,
            headers={
                "Accept": "application/json",
                "Cookie": self.cookie,
                "User-Agent": user_agent,
                "Origin": CHATIK_BASE,
                "Referer": f"{CHATIK_BASE}/?platform=xhh&dest=iframe",
                "X-Requested-With": "XMLHttpRequest",
                "X-XSRFToken": self.xsrf,
                "X-XsrfToken": self.xsrf,
            },
            timeout=60.0,
            follow_redirects=True,
        )
        self._applicant_id: str | None = None

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ChatikClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def chat_url(self, chat_id: str) -> str:
        return f"{self.hh_host}/chat/{chat_id}"

    def vacancy_url(self, vacancy_id: str) -> str:
        return f"{self.hh_host}/vacancy/{vacancy_id}"

    def topic_url(self, topic_id: str) -> str:
        return f"{self.hh_host}/applicant/negotiations?topicId={topic_id}"

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        optional: bool = False,
        retries: int = 4,
    ) -> dict[str, Any] | None:
        last_error: Exception | None = None
        for attempt in range(max(1, retries)):
            time.sleep(self.delay if attempt == 0 else min(8.0, self.delay * (2**attempt) + 0.4))
            try:
                resp = self._client.get(path, params=params)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt + 1 >= retries:
                    if optional:
                        return None
                    raise HhApiError(f"Chatik network error {path}: {exc}") from exc
                continue

            if resp.status_code in (401, 403):
                if optional:
                    return None
                raise HhAuthError(
                    f"Сессия недействительна ({resp.status_code}). "
                    "Обновите cookie из браузера после входа на hh.ru."
                )
            if resp.status_code in (429, 500, 502, 503, 504):
                last_error = HhApiError(
                    f"Chatik temporary {resp.status_code} {path}: {resp.text[:200]}"
                )
                if attempt + 1 >= retries:
                    if optional:
                        return None
                    raise last_error
                continue
            if resp.status_code >= 400:
                if optional:
                    return None
                raise HhApiError(f"Chatik error {resp.status_code} {path}: {resp.text[:500]}")
            if not resp.content:
                return {}
            try:
                return resp.json()
            except Exception as exc:
                if optional:
                    return None
                raise HhApiError(f"Chatik invalid JSON {path}: {exc}") from exc

        if optional:
            return None
        if last_error:
            raise last_error
        return None

    def get_applicant_id(self) -> str | None:
        if self._applicant_id is not None:
            return self._applicant_id or None

        hi = cookie_value(self.cookie, "_hi")
        if hi.isdigit():
            self._applicant_id = hi
            return self._applicant_id

        data = self._get(
            "/chatik/api/participants/me",
            params={"do_not_track_session_events": "true"},
            optional=True,
        )
        if not data:
            self._applicant_id = ""
            return None

        for key in ("id", "participantId", "userId", "applicantId"):
            if data.get(key) is not None:
                self._applicant_id = str(data[key])
                return self._applicant_id
        participant = data.get("participant") or data.get("me") or {}
        if isinstance(participant, dict):
            for key in ("id", "participantId", "userId"):
                if participant.get(key) is not None:
                    self._applicant_id = str(participant[key])
                    return self._applicant_id
        self._applicant_id = ""
        return None

    def iter_chats(
        self,
        since: datetime,
        on_page: Callable[[int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page = 0
        while True:
            data = self._get(
                "/chatik/api/chats",
                params={
                    "filterUnread": "false",
                    "filterHasTextMessage": "false",
                    "do_not_track_session_events": "true",
                    "page": page,
                },
            )
            chats_block = (data or {}).get("chats") or {}
            chunk = chats_block.get("items") or []
            display = (data or {}).get("chatsDisplayInfo") or {}
            resources = (data or {}).get("resources") or {}
            if not chunk:
                break

            stop = False
            for chat in chunk:
                activity = parse_dt(chat.get("lastActivityTime")) or parse_dt(
                    (chat.get("lastMessage") or {}).get("creationTime")
                )
                if activity is not None and activity < since:
                    stop = True
                    break
                chat_id = str(chat.get("id") or "")
                items.append(
                    {
                        "chat": chat,
                        "display": display.get(chat_id) or display.get(str(chat.get("id"))) or {},
                        "list_resources": resources,
                    }
                )

            if on_page is not None:
                on_page(page, len(items))

            pages = chats_block.get("pages")
            if stop:
                break
            if pages is not None:
                if page >= pages - 1:
                    break
            elif not chunk:
                break
            page += 1
        return items

    def get_chat_data(self, chat_id: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "chatId": chat_id,
            "do_not_track_session_events": "true",
        }
        applicant_id = self.get_applicant_id()
        data: dict[str, Any] | None = None
        if applicant_id:
            params["applicantId"] = applicant_id
            data = self._get("/chatik/api/chat_data", params=params, optional=True)
            if data is None:
                params.pop("applicantId", None)
                data = self._get("/chatik/api/chat_data", params=params)
        else:
            data = self._get("/chatik/api/chat_data", params=params)
        data = data or {}
        return self._paginate_messages(chat_id, data, params)

    def _paginate_messages(
        self,
        chat_id: str,
        data: dict[str, Any],
        base_params: dict[str, Any],
    ) -> dict[str, Any]:
        """Дочитывает страницы messages, если Chatik отдал pages > 1."""
        messages = data.get("messages")
        if not isinstance(messages, dict):
            return data
        items = list(messages.get("items") or [])
        pages = messages.get("pages")
        try:
            page_count = int(pages) if pages is not None else 1
        except (TypeError, ValueError):
            page_count = 1
        if page_count <= 1:
            return data

        for page in range(1, min(page_count, 20)):
            page_params = dict(base_params)
            page_params["chatId"] = chat_id
            page_params["page"] = page
            more = self._get("/chatik/api/chat_data", params=page_params, optional=True)
            if not more:
                break
            block = more.get("messages") or {}
            chunk = block.get("items") if isinstance(block, dict) else None
            if not chunk:
                break
            items.extend(chunk)
        messages["items"] = items
        data["messages"] = messages
        return data
