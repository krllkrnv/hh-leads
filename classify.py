"""Классификация чатов hh: паттерны, действия, ChatRecord."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from hh_client import ChatikClient, parse_dt

INVITE_PATTERNS = [
    r"приглаша",
    r"приглашени",
    r"собеседован",
    r"интервью",
    r"\binterview\b",
    r"\bzoom\b",
    r"\bteams\b",
    r"\bmeet\.google\b",
    r"google meet",
    r"созвон",
    r"встреч[аиуеы]",
    r"телефонн(ое|ого|ый)\s+(интервью|разговор|звонок)",
    r"назнач\w*\s+встреч",
    r"приглас\w*\s+на\s+(собесед|интервью|встреч)",
    r"позвон\w*",
    r"перезвон\w*",
    r"набер\w*",
    r"свяж(итесь|ёмся|емся)",
    r"связаться",
    r"напиш(ите|и)",
    r"\bпишите\b",
    r"написать\s+(мне|нам|в|на)",
    r"жду\s+(ваш\s+)?(звонок|ответ|сообщен)",
    r"удобно\s+(ли\s+)?(созвон|позвон|созвониться|позвонить|созвон)",
    r"телефон",
    r"\bтел\.?\s*[:\-]?\s*\+?\d",
    r"\+7[\s\-]?\(?\d{3}\)?",
    r"телеграм|telegram|\btg\b",
    r"@\w{3,}",
    r"whats?app|ватсап|вотсап|вацап",
    r"контакт(ы|ный|ная)?",
    r"на\s+связи",
    r"оста(вьте|вить)\s+(свой\s+)?(номер|телефон|контакт|email|почт)",
    r"ваш(а|у)?\s+(почт|email|номер|телефон)",
    r"скинь(те)?\s+(номер|телефон|контакт)",
]

TEST_PATTERNS = [
    r"тестов(ое|ого|ый|ому|ым)\s+задани",
    r"test\s*task",
    r"домашн\w*\s+задани",
    r"\bhomework\b",
    r"\bcase[\s-]?(study|task)?\b",
    r"кейс[\s-]задани",
    r"выполн\w*\s+задани",
    r"сделать\s+задани",
    r"пришлите\s+решени",
    r"тестов(ая|ую)\s+работ",
    r"пройт\w*\s+тестов",
]

# Явная просьба связаться с кандидатом (для тега call в дашборде)
STRONG_CONTACT_PATTERNS = [
    r"\b(пожалуйста[, ]+)?(позвоните|перезвоните|наберите)\b",
    r"свяжитесь",
    r"напиш(ите|и)\s+(мне|нам|в|на|пожалуйста)",
    r"\bпишите\b\s+(мне|нам|в|на)",
    r"написать\s+(мне|нам|в|на)",
    r"жду\s+(ваш\s+)?звонок",
    r"удобно\s+(ли\s+)?(созвон|позвон|созвониться|позвонить)",
    r"телефонн(ое|ый)\s+(интервью|разговор|звонок)",
    r"\bтел\.?\s*[:\-]?\s*\+?\d",
    r"\+7[\s\-]?\(?\d{3}\)?",
    r"(телеграм|telegram|\btg\b).{0,40}@?\w{3,}",
    r"whats?app|ватсап|вотсап|вацап",
    r"оста(вьте|вить)\s+(свой\s+)?(номер|телефон|контакт)",
]

CLOSED_PATTERNS = [
    r"уже закрыл",
    r"вакансия закрыт",
    r"не актуал",
    r"отозвал",
]

STATE_NAMES = {
    "response": "Отклик",
    "invitation": "Приглашение",
    "interview": "Собеседование",
    "discard": "Отказ",
    "hired": "Выход на работу",
    "hidden": "Скрытый",
}

ACTION_PRIORITY = {
    "Ответить работодателю": 10,
    "Собеседование / встреча": 20,
    "Тестовое задание": 30,
    "Ждать ответа HR": 40,
    "Автоответ / бот": 50,
    "Отказ / закрыто": 60,
    "Без действия": 70,
}


def compile_patterns(patterns: Iterable[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns]


INVITE_RE = compile_patterns(INVITE_PATTERNS)
TEST_RE = compile_patterns(TEST_PATTERNS)
STRONG_CONTACT_RE = compile_patterns(STRONG_CONTACT_PATTERNS)
CLOSED_RE = compile_patterns(CLOSED_PATTERNS)


@dataclass
class ChatRecord:
    negotiation_id: str
    company: str
    vacancy_name: str
    vacancy_url: str
    chat_url: str
    state_id: str
    state_name: str
    updated_at: datetime | None
    first_message_at: datetime | None
    summary: str
    invite_reasons: list[str] = field(default_factory=list)
    test_reasons: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    action: str = "Без действия"
    action_detail: str = ""
    last_from: str = ""
    strong_contact: bool = False
    vacancy_closed: bool = False

    def reasons_for(self, category: str) -> str:
        if category == "Приглашения":
            return "; ".join(self.invite_reasons)
        if category == "Тестовые":
            return "; ".join(self.test_reasons)
        if category == "Обсуждения":
            return "остальная переписка / без признаков приглашения и теста"
        return ""

    def extra_categories(self, current: str) -> str:
        others = [c for c in self.categories if c != current]
        return ", ".join(others)


def first_resource_id(resources: dict[str, Any], key: str) -> str | None:
    vals = resources.get(key) if isinstance(resources, dict) else None
    if isinstance(vals, list) and vals:
        return str(vals[0])
    return None


def lookup_map(mapping: Any, key: str | None) -> dict[str, Any]:
    if not key or not isinstance(mapping, dict):
        return {}
    val = mapping.get(key) or mapping.get(str(key))
    return val if isinstance(val, dict) else {}


def extract_meta(
    chat: dict[str, Any],
    display: dict[str, Any],
    list_resources: dict[str, Any],
    chat_data: dict[str, Any] | None = None,
    *,
    client: ChatikClient | None = None,
) -> dict[str, Any]:
    chat_id = str(chat.get("id") or "")
    chat_res = chat.get("resources") or {}
    vacancy_id = first_resource_id(chat_res, "VACANCY")
    topic_id = first_resource_id(chat_res, "NEGOTIATION_TOPIC")

    ext = (chat_data or {}).get("resources") or {}
    vacancies = ext.get("vacancies") or list_resources.get("vacancies") or {}
    employers = ext.get("employers") or list_resources.get("employers") or {}
    topics = (
        ext.get("negotiation_topics")
        or ext.get("negotiationTopics")
        or list_resources.get("negotiation_topics")
        or {}
    )

    vacancy = lookup_map(vacancies, vacancy_id)
    company_obj = vacancy.get("company") if isinstance(vacancy.get("company"), dict) else {}
    company = str(
        company_obj.get("visibleName")
        or company_obj.get("name")
        or display.get("title")
        or ""
    )
    if not company and isinstance(employers, dict) and employers:
        first_emp = next(iter(employers.values()), None)
        if isinstance(first_emp, dict):
            company = str(first_emp.get("visibleName") or first_emp.get("name") or "")

    vacancy_name = str(vacancy.get("name") or display.get("subtitle") or "")
    links = vacancy.get("links") if isinstance(vacancy.get("links"), dict) else {}
    vacancy_url = str(links.get("desktop") or "")
    if client:
        if not vacancy_url and vacancy_id:
            vacancy_url = client.vacancy_url(vacancy_id)
        elif not vacancy_url and vacancy.get("vacancyId"):
            vacancy_url = client.vacancy_url(str(vacancy["vacancyId"]))
        chat_url = client.chat_url(chat_id) if chat_id else (
            client.topic_url(topic_id) if topic_id else ""
        )
    else:
        host = "https://hh.ru"
        if not vacancy_url and vacancy_id:
            vacancy_url = f"{host}/vacancy/{vacancy_id}"
        elif not vacancy_url and vacancy.get("vacancyId"):
            vacancy_url = f"{host}/vacancy/{vacancy['vacancyId']}"
        chat_url = f"{host}/chat/{chat_id}" if chat_id else (
            f"{host}/applicant/negotiations?topicId={topic_id}" if topic_id else ""
        )

    topic = lookup_map(topics, topic_id)
    state_id = str(
        topic.get("currentApplicantState") or topic.get("currentTopicType") or ""
    ).lower()
    for candidate in (
        topic.get("currentApplicantState"),
        topic.get("currentTopicType"),
        topic.get("initialApplicantState"),
    ):
        if isinstance(candidate, str) and candidate.lower() in STATE_NAMES:
            state_id = candidate.lower()
            break

    has_test = bool(ext.get("test_solutions") or ext.get("testSolutions"))
    if isinstance(vacancy.get("userTestPresent"), bool) and vacancy["userTestPresent"]:
        has_test = True

    updated_at = parse_dt(chat.get("lastActivityTime")) or parse_dt(
        (chat.get("lastMessage") or {}).get("creationTime")
    )

    return {
        "id": chat_id,
        "topic_id": topic_id or "",
        "company": company,
        "vacancy_name": vacancy_name,
        "vacancy_url": vacancy_url,
        "chat_url": chat_url,
        "state_id": state_id,
        "state_name": STATE_NAMES.get(state_id, state_id),
        "updated_at": updated_at,
        "has_test_resource": has_test,
    }


def extract_messages(
    chat_data: dict[str, Any],
    my_participant_id: str | None = None,
) -> list[dict[str, Any]]:
    chat = chat_data.get("chat") or {}
    if not my_participant_id:
        my_participant_id = str(chat.get("currentParticipantId") or "") or None
    messages_block = chat.get("messages") or {}
    items = messages_block.get("items") or []
    out: list[dict[str, Any]] = []
    for msg in items:
        if not isinstance(msg, dict):
            continue
        text = str(msg.get("text") or "").strip()
        wt = msg.get("workflowTransition")
        if isinstance(wt, dict):
            state = wt.get("applicantState")
            if state:
                text = f"{text}\n{state}".strip()
        display = msg.get("participantDisplay") or {}
        author = ""
        is_bot = False
        if isinstance(display, dict):
            author = str(display.get("name") or "")
            is_bot = bool(display.get("isBot"))
            if is_bot:
                author = author or "bot"
        participant_id = str(msg.get("participantId") or "")
        author = author or participant_id
        is_me = False
        if my_participant_id and participant_id and participant_id == str(my_participant_id):
            is_me = True
        if msg.get("own") is True or msg.get("isOwn") is True:
            is_me = True
        out.append(
            {
                "text": text,
                "created_at": msg.get("creationTime"),
                "author": author,
                "participant_id": participant_id,
                "is_bot": is_bot,
                "is_me": is_me,
                "workflow_state": (wt or {}).get("applicantState")
                if isinstance(wt, dict)
                else None,
            }
        )
    return out


def message_text(msg: dict[str, Any]) -> str:
    return str(msg.get("text") or "").strip()


def message_author(msg: dict[str, Any]) -> str:
    return str(msg.get("author") or "")


def last_meaningful_message(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    for msg in reversed(messages):
        if message_text(msg) or msg.get("workflow_state"):
            return msg
    return messages[-1] if messages else None


def detect_action(
    meta: dict[str, Any],
    messages: list[dict[str, Any]],
    invite_reasons: list[str],
    test_reasons: list[str],
) -> tuple[str, str, str]:
    state_id = str(meta.get("state_id") or "").lower()
    last = last_meaningful_message(messages)
    if not last:
        if state_id in ("discard", "hidden"):
            return "Отказ / закрыто", "нет сообщений", ""
        return "Без действия", "нет сообщений", ""

    if last.get("is_me"):
        last_from = "я"
    elif last.get("is_bot"):
        last_from = "бот"
    else:
        last_from = "работодатель"

    last_text = message_text(last)
    author = message_author(last) or last_from
    closed = state_id in ("discard", "hidden")

    if invite_reasons:
        detail = "; ".join(invite_reasons[:3])
        if closed:
            detail = f"статус {state_id}; {detail}"
        if last_from == "работодатель":
            return (
                "Собеседование / встреча",
                f"нужен ответ или подтверждение · {detail}",
                last_from,
            )
        return (
            "Собеседование / встреча",
            f"ждём/уже ответили · {detail}",
            last_from,
        )

    if test_reasons or meta.get("has_test_resource"):
        detail = "; ".join(test_reasons[:3]) or "тестовое в ресурсах"
        if closed:
            detail = f"статус {state_id}; {detail}"
        if last_from == "работодатель":
            return "Тестовое задание", f"похоже, ждут решение · {detail}", last_from
        return "Тестовое задание", f"тест в переписке · {detail}", last_from

    if closed:
        return "Отказ / закрыто", f"статус {state_id}; последний: {author}", last_from

    if last_from == "работодатель":
        snippet = re.sub(r"\s+", " ", last_text)[:120]
        return "Ответить работодателю", f"последнее от HR: {snippet}", last_from

    if last_from == "бот":
        snippet = re.sub(r"\s+", " ", last_text)[:120]
        return "Автоответ / бот", f"бот: {snippet}", last_from

    if last_from == "я":
        return "Ждать ответа HR", f"последнее от тебя · {author}", last_from

    return "Без действия", "", last_from


def build_summary(messages: list[dict[str, Any]], limit: int = 5, max_len: int = 200) -> str:
    if not messages:
        return ""
    tail = messages[-limit:]
    lines: list[str] = []
    for msg in tail:
        author = message_author(msg) or "?"
        if msg.get("is_me"):
            author = "я"
        text = re.sub(r"\s+", " ", message_text(msg)).strip()
        if not text:
            continue
        if len(text) > max_len:
            text = text[: max_len - 1] + "…"
        lines.append(f"[{author}] {text}")
    return " | ".join(lines)


def match_reasons(text: str, patterns: list[re.Pattern[str]]) -> list[str]:
    found: list[str] = []
    for pat in patterns:
        m = pat.search(text)
        if m:
            found.append(m.group(0))
    seen: set[str] = set()
    out: list[str] = []
    for item in found:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def employer_corpus(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for m in messages:
        if m.get("is_me"):
            continue
        text = message_text(m)
        if text:
            parts.append(text)
        ws = m.get("workflow_state")
        if ws:
            parts.append(str(ws))
    return "\n".join(parts)


def classify(meta: dict[str, Any], messages: list[dict[str, Any]]) -> ChatRecord:
    state_id = str(meta.get("state_id") or "")
    company = str(meta.get("company") or "")
    vacancy_name = str(meta.get("vacancy_name") or "")

    timestamps = [parse_dt(m.get("created_at")) for m in messages]
    timestamps = [t for t in timestamps if t is not None]
    first_message_at = min(timestamps) if timestamps else None
    updated_at = meta.get("updated_at")
    if not isinstance(updated_at, datetime):
        updated_at = parse_dt(updated_at)

    corpus = employer_corpus(messages)
    invite_reasons: list[str] = []
    test_reasons: list[str] = []

    state_lower = state_id.lower()
    if state_lower in ("invitation", "interview"):
        invite_reasons.append(f"статус: {state_lower}")

    invite_reasons.extend(f"текст: «{r}»" for r in match_reasons(corpus, INVITE_RE))
    test_reasons.extend(f"текст: «{r}»" for r in match_reasons(corpus, TEST_RE))
    if meta.get("has_test_resource"):
        test_reasons.append("ресурс test_solutions / userTestPresent")

    invite_reasons = list(dict.fromkeys(invite_reasons))
    test_reasons = list(dict.fromkeys(test_reasons))

    categories: list[str] = []
    if invite_reasons:
        categories.append("Приглашения")
    if test_reasons:
        categories.append("Тестовые")
    if not categories:
        if messages or company or vacancy_name:
            categories.append("Обсуждения")
    if not categories:
        categories.append("Обсуждения")

    action, action_detail, last_from = detect_action(
        meta, messages, invite_reasons, test_reasons
    )
    blob = f"{corpus}\n{action_detail}\n{build_summary(messages)}"
    strong_contact = bool(match_reasons(corpus, STRONG_CONTACT_RE))
    vacancy_closed = bool(match_reasons(blob, CLOSED_RE))

    return ChatRecord(
        negotiation_id=str(meta.get("id") or ""),
        company=company,
        vacancy_name=vacancy_name,
        vacancy_url=str(meta.get("vacancy_url") or ""),
        chat_url=str(meta.get("chat_url") or ""),
        state_id=state_id,
        state_name=STATE_NAMES.get(state_id, state_id) or str(meta.get("state_name") or ""),
        updated_at=updated_at,
        first_message_at=first_message_at,
        summary=build_summary(messages),
        invite_reasons=invite_reasons,
        test_reasons=test_reasons,
        categories=categories,
        action=action,
        action_detail=action_detail,
        last_from=last_from,
        strong_contact=strong_contact,
        vacancy_closed=vacancy_closed,
    )
