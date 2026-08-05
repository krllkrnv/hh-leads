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


class SyncCancelled(Exception):
    """Пользователь остановил синхронизацию (list или fetch)."""


_COOKIE_META = frozenset(
    {
        "domain",
        "expires",
        "path",
        "samesite",
        "secure",
        "httponly",
        "hostonly",
        "value",
        "size",
        "priority",
        "sameparty",
        "partitioned",
    }
)

_COOKIE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _strip_wrapping_quotes(text: str) -> str:
    value = text.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _is_cookie_name(name: str) -> bool:
    key = name.strip()
    if not key or key.lower() in _COOKIE_META:
        return False
    return bool(_COOKIE_NAME_RE.match(key))


def parse_cookie_map(raw: str) -> dict[str, str]:
    """
    Достаёт пары cookie из разных форматов вставки:
    - заголовок Cookie: hhtoken=…; _xsrf=…
    - таблица Application → Cookies (name / value / domain…)
    - строки name\\tvalue
    """
    text = raw.strip()
    if not text:
        return {}

    if text.lower().startswith("cookie:"):
        text = text.split(":", 1)[1].strip()
    text = _strip_wrapping_quotes(text)

    found: dict[str, str] = {}

    def put(name: str, value: str) -> None:
        key = name.strip()
        val = _strip_wrapping_quotes(value)
        if not _is_cookie_name(key) or not val:
            return
        # Не затираем уже найденный непустой токен более коротким мусором
        if key in found and len(found[key]) >= len(val):
            return
        found[key] = val

    # 1) Классика: key=value; key=value (в т.ч. с переносами)
    for part in re.split(r"[;\n\r]+", text):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, val = part.split("=", 1)
        key = key.strip()
        # Отсекаем meta-строки дампа (domain=.hh.ru)
        if key.lower() in _COOKIE_META:
            continue
        if "\t" in key or " " in key:
            continue
        put(key, val)

    # 2) Строки name<TAB>value / name<TAB>"value"
    for match in re.finditer(
        r'(?m)^([A-Za-z0-9_.-]+)\t+"?([^\t\n\r"]+)"?\s*$',
        text,
    ):
        put(match.group(1), match.group(2))

    # 3) Дамп Storage: имя cookie, ниже блок domain/path/value
    lines = [line.strip() for line in text.splitlines()]
    for index, line in enumerate(lines):
        if not _is_cookie_name(line):
            continue
        for look in range(index + 1, min(index + 10, len(lines))):
            nxt = lines[look]
            if not nxt:
                continue
            value_match = re.match(r'^value\t+"?(.*?)"?\s*$', nxt, flags=re.IGNORECASE)
            if value_match:
                put(line, value_match.group(1))
                break
            # Следующее имя cookie без meta — блок закончился
            if _is_cookie_name(nxt) and nxt.lower() not in _COOKIE_META:
                break
            eq_match = re.match(r'^value\s*[:=]\s*"?(.*?)"?\s*$', nxt, flags=re.IGNORECASE)
            if eq_match:
                put(line, eq_match.group(1))
                break

    # 4) Запасной regex по ключевым полям
    for name in ("hhtoken", "_xsrf", "hhuid", "_hi", "crypted_id", "hhrole", "redirect_host"):
        if name in found:
            continue
        match = re.search(
            rf'(?im)(?:^|[\s;]){re.escape(name)}\s*[=\t:]\s*"?([^\s";]+)"?',
            text,
        )
        if match:
            put(name, match.group(1))

    return found


def normalize_cookie(raw: str) -> str:
    """Приводит любой вставленный дамп к строке Cookie-заголовка."""
    mapping = parse_cookie_map(raw)
    if not mapping:
        text = raw.strip()
        if text.lower().startswith("cookie:"):
            text = text.split(":", 1)[1].strip()
        return _strip_wrapping_quotes(text)

    preferred = (
        "hhtoken",
        "_xsrf",
        "hhuid",
        "_hi",
        "crypted_id",
        "hhrole",
        "redirect_host",
    )
    parts: list[str] = []
    seen: set[str] = set()
    for key in preferred:
        if key in mapping:
            parts.append(f"{key}={mapping[key]}")
            seen.add(key)
    for key, value in mapping.items():
        if key in seen:
            continue
        parts.append(f"{key}={value}")
    return "; ".join(parts)


def cookie_value(cookie: str, name: str) -> str:
    # Сначала как готовая Cookie-строка
    for part in cookie.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, val = part.split("=", 1)
        if key.strip() == name:
            return unquote(_strip_wrapping_quotes(val))
    # Если передали сырой дамп до normalize
    mapped = parse_cookie_map(cookie)
    if name in mapped:
        return unquote(mapped[name])
    return ""


def suggest_hh_host_from_cookie(cookie: str) -> str | None:
    """Достаёт redirect_host / region_clarified из cookie, если есть."""
    mapping = parse_cookie_map(cookie)
    for key in ("redirect_host", "region_clarified"):
        host = mapping.get(key, "").strip()
        if host:
            return normalize_hh_host(host)
    return None


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
            raise HhAuthError(
                "Не нашли hhtoken во вставленном тексте. "
                "Скопируй cookie из Application → Cookies или строку Cookie из Network."
            )
        if not self.xsrf:
            raise HhAuthError(
                "Не нашли _xsrf во вставленном тексте. "
                "Нужны и hhtoken, и _xsrf — вставь дамп целиком."
            )

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
        should_cancel: Callable[[], bool] | None = None,
    ) -> list[dict[str, Any]]:
        """Список чатов, у которых последняя активность не старше since.

        После страницы, где встретился более старый чат, следующие страницы
        не запрашиваем (Chatik обычно отдаёт список от новых к старым).
        Внутри страницы смотрим все элементы: «молодые» после «старых»
        не теряем. Чаты без даты активности в окно не попадают.
        """
        items: list[dict[str, Any]] = []
        page = 0
        while True:
            if should_cancel is not None and should_cancel():
                raise SyncCancelled("Синхронизация отменена")

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
                if activity is None:
                    continue
                if activity < since:
                    stop = True
                    continue
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
        """Дочитывает следующие страницы сообщений, если их больше одной.

        Блок messages может лежать на верхнем уровне ответа или внутри chat.
        """
        messages, owner, key = resolve_messages_block(data)
        if messages is None or owner is None or key is None:
            return data
        items = list(messages.get("items") or [])
        pages = messages.get("pages")
        try:
            page_count = int(pages) if pages is not None else 1
        except (TypeError, ValueError):
            page_count = 1
        if page_count <= 1:
            return data

        # Длинные треды: дочитываем до 40 страниц, дальше почти не бывает.
        for page in range(1, min(page_count, 40)):
            page_params = dict(base_params)
            page_params["chatId"] = chat_id
            page_params["page"] = page
            more = self._get("/chatik/api/chat_data", params=page_params, optional=True)
            if not more:
                break
            block, _, _ = resolve_messages_block(more)
            chunk = block.get("items") if isinstance(block, dict) else None
            if not chunk:
                break
            items.extend(chunk)
        messages["items"] = items
        owner[key] = messages
        # Дублируем в оба места: extract_messages умеет читать и top-level, и chat.messages.
        data["messages"] = messages
        chat = data.get("chat")
        if isinstance(chat, dict):
            chat["messages"] = messages
        return data


def resolve_messages_block(
    chat_data: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    """Ищет блок messages в ответе chat_data: сверху или внутри chat.

    Возвращает сам блок, словарь-владельца и ключ, либо тройку None.
    """
    top = chat_data.get("messages")
    if isinstance(top, dict) and (top.get("items") is not None or top.get("pages") is not None):
        return top, chat_data, "messages"
    chat = chat_data.get("chat")
    if isinstance(chat, dict):
        nested = chat.get("messages")
        if isinstance(nested, dict):
            return nested, chat, "messages"
    if isinstance(top, dict):
        return top, chat_data, "messages"
    return None, None, None
