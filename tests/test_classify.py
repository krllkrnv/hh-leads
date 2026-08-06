"""Тесты классификации и извлечения сообщений."""

from __future__ import annotations

from hh_leads.classify import classify, extract_messages, match_reasons, INVITE_RE
from hh_leads.hh_client import resolve_messages_block
from hh_leads.report import lead_tag
from tests.test_report_buckets import _rec


def test_resolve_messages_top_level() -> None:
    data = {"messages": {"items": [{"text": "hi"}], "pages": 1}, "chat": {}}
    block, owner, key = resolve_messages_block(data)
    assert block is not None
    assert key == "messages"
    assert owner is data
    assert len(block["items"]) == 1


def test_resolve_messages_nested_in_chat() -> None:
    data = {"chat": {"messages": {"items": [{"text": "nested"}], "pages": 2}}}
    block, owner, key = resolve_messages_block(data)
    assert block is not None
    assert owner is data["chat"]
    assert block["items"][0]["text"] == "nested"


def test_extract_messages_reads_top_level() -> None:
    data = {
        "chat": {"currentParticipantId": "me"},
        "messages": {
            "items": [
                {
                    "text": "Приглашаем на собеседование",
                    "participantId": "hr",
                    "creationTime": "2024-01-01T12:00:00+03:00",
                    "participantDisplay": {"name": "HR"},
                }
            ]
        },
    }
    msgs = extract_messages(data)
    assert len(msgs) == 1
    assert "Приглашаем" in msgs[0]["text"]
    assert msgs[0]["is_me"] is False


def test_extract_messages_reads_nested() -> None:
    data = {
        "chat": {
            "currentParticipantId": "me",
            "messages": {
                "items": [
                    {
                        "text": "ok",
                        "participantId": "me",
                        "own": True,
                        "participantDisplay": {"name": "Я"},
                    }
                ]
            },
        }
    }
    msgs = extract_messages(data)
    assert len(msgs) == 1
    assert msgs[0]["is_me"] is True


def test_invite_not_triggered_by_na_svyazi_alone() -> None:
    assert not match_reasons("Мы всегда на связи с клиентами", INVITE_RE)
    assert match_reasons("мы на связи, позвоните", INVITE_RE)


def test_invite_not_triggered_by_zhdu_otvet() -> None:
    assert not match_reasons("жду ваш ответ по вакансии", INVITE_RE)
    assert match_reasons("жду ваш звонок завтра", INVITE_RE)


def test_classify_invite_from_employer() -> None:
    meta = {
        "id": "1",
        "company": "Acme",
        "vacancy_name": "Dev",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/1",
        "state_id": "response",
        "state_name": "Отклик",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "Приглашаем вас на собеседование в Zoom",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        }
    ]
    rec = classify(meta, messages)
    assert "Приглашения" in rec.categories
    assert rec.action == "Собеседование / встреча"
    assert lead_tag(rec) == "interview"


def test_classify_user_ne_aktualno_does_not_close() -> None:
    meta = {
        "id": "2",
        "company": "Beta",
        "vacancy_name": "QA",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/2",
        "state_id": "response",
        "state_name": "Отклик",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "Добрый день, вакансия ещё открыта?",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        },
        {
            "text": "Спасибо, уже не актуально для меня",
            "created_at": "2024-06-01T11:00:00+03:00",
            "author": "я",
            "is_me": True,
            "is_bot": False,
            "workflow_state": None,
        },
    ]
    rec = classify(meta, messages)
    assert rec.vacancy_closed is False
    assert lead_tag(rec) == "wait"


def test_classify_employer_vacancy_closed() -> None:
    meta = {
        "id": "3",
        "company": "Gamma",
        "vacancy_name": "PM",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/3",
        "state_id": "response",
        "state_name": "Отклик",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "К сожалению, вакансия закрыта",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        }
    ]
    rec = classify(meta, messages)
    assert rec.vacancy_closed is True
    assert lead_tag(rec) == "closed"


def test_lead_tag_strong_contact_over_reply() -> None:
    rec = _rec(
        action="Ответить работодателю",
        strong_contact=True,
        last_from="работодатель",
    )
    assert lead_tag(rec) == "call"


def test_classify_test_task() -> None:
    meta = {
        "id": "4",
        "company": "Delta",
        "vacancy_name": "FE",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/4",
        "state_id": "response",
        "state_name": "Отклик",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "Пришлите решение тестового задания до пятницы",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        }
    ]
    rec = classify(meta, messages)
    assert "Тестовые" in rec.categories
    assert rec.action == "Тестовое задание"
    assert lead_tag(rec) == "test"


def test_discard_beats_old_invite() -> None:
    meta = {
        "id": "5",
        "company": "Eps",
        "vacancy_name": "BE",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/5",
        "state_id": "discard",
        "state_name": "Отказ",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "Приглашаем на собеседование",
            "created_at": "2024-05-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        }
    ]
    rec = classify(meta, messages)
    assert "Приглашения" in rec.categories  # след в истории
    assert rec.action == "Отказ / закрыто"
    assert rec.vacancy_closed is True
    assert lead_tag(rec) == "closed"


def test_invite_then_user_reply_is_wait() -> None:
    meta = {
        "id": "6",
        "company": "Zeta",
        "vacancy_name": "Dev",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/6",
        "state_id": "invitation",
        "state_name": "Приглашение",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "Приглашаем на собеседование в Zoom",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        },
        {
            "text": "Спасибо, буду в 15:00",
            "created_at": "2024-06-01T11:00:00+03:00",
            "author": "я",
            "is_me": True,
            "is_bot": False,
            "workflow_state": None,
        },
    ]
    rec = classify(meta, messages)
    assert "Приглашения" in rec.categories
    assert rec.action == "Ждать ответа HR"
    assert lead_tag(rec) == "wait"


def test_test_then_user_reply_is_wait() -> None:
    meta = {
        "id": "7",
        "company": "Eta",
        "vacancy_name": "FE",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/7",
        "state_id": "response",
        "state_name": "Отклик",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "Нужно тестовое задание",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        },
        {
            "text": "Отправил решение",
            "created_at": "2024-06-01T12:00:00+03:00",
            "author": "я",
            "is_me": True,
            "is_bot": False,
            "workflow_state": None,
        },
    ]
    rec = classify(meta, messages)
    assert "Тестовые" in rec.categories
    assert rec.action == "Ждать ответа HR"
    assert lead_tag(rec) == "wait"


def test_lead_tag_wait_beats_strong_and_invite_category() -> None:
    rec = _rec(
        action="Ждать ответа HR",
        strong_contact=True,
        categories=["Приглашения"],
        invite_reasons=["текст: «собеседование»"],
        last_from="я",
    )
    assert lead_tag(rec) == "wait"


def test_text_closed_beats_invite() -> None:
    meta = {
        "id": "8",
        "company": "Theta",
        "vacancy_name": "QA",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/8",
        "state_id": "invitation",
        "state_name": "Приглашение",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "Приглашаем на интервью. К сожалению, вакансия закрыта",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        }
    ]
    rec = classify(meta, messages)
    assert rec.action == "Отказ / закрыто"
    assert lead_tag(rec) == "closed"


def test_svyazhemsya_template_is_not_invite() -> None:
    """Шаблон «рассмотрим и свяжемся» — не live invite."""
    assert not match_reasons(
        "Спасибо за отклик! Мы рассмотрим резюме и свяжемся с вами.",
        INVITE_RE,
    )
    assert not match_reasons("Свяжемся в ближайшее время.", INVITE_RE)
    assert match_reasons("Пожалуйста, свяжитесь с нами по телефону", INVITE_RE)

    meta = {
        "id": "9",
        "company": "Iota",
        "vacancy_name": "FE",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/9",
        "state_id": "response",
        "state_name": "Отклик",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": (
                "Здравствуйте! Компания рассмотрит Ваше резюме и позже "
                "сообщит Вам о своем решении. Свяжемся с вами."
            ),
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        }
    ]
    rec = classify(meta, messages)
    assert "Приглашения" not in rec.categories
    assert rec.action == "Ответить работодателю"
    assert lead_tag(rec) == "reply"


def test_svyazhites_still_invite_and_call() -> None:
    meta = {
        "id": "10",
        "company": "Kappa",
        "vacancy_name": "FE",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/10",
        "state_id": "response",
        "state_name": "Отклик",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "Добрый день! Свяжитесь с нами, пожалуйста",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        }
    ]
    rec = classify(meta, messages)
    assert "Приглашения" in rec.categories
    assert rec.strong_contact is True
    assert rec.action == "Собеседование / встреча"


def test_interview_status_still_invite_with_svyazhemsya() -> None:
    """Статус interview — hard signal; шаблон «свяжемся» рядом не ломает."""
    meta = {
        "id": "11",
        "company": "Lambda",
        "vacancy_name": "FE",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/11",
        "state_id": "interview",
        "state_name": "Собеседование",
        "updated_at": None,
        "has_test_resource": False,
    }
    messages = [
        {
            "text": "Мы рассмотрим резюме и свяжемся",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "HR",
            "is_me": False,
            "is_bot": False,
            "workflow_state": None,
        }
    ]
    rec = classify(meta, messages)
    assert "Приглашения" in rec.categories
    assert any("статус: interview" in r for r in rec.invite_reasons)
    assert rec.action == "Собеседование / встреча"


def test_vacancy_test_flag_alone_not_category() -> None:
    """userTestPresent / test_solutions без текста HR не дают «Тестовые»."""
    meta = {
        "id": "12",
        "company": "Московская Биржа",
        "vacancy_name": "Frontend-разработчик",
        "vacancy_url": "",
        "chat_url": "https://hh.ru/chat/12",
        "state_id": "response",
        "state_name": "Отклик",
        "updated_at": None,
        "has_test_resource": True,
    }
    messages = [
        {
            "text": "Здравствуйте! Три года frontend. Telegram: @user",
            "created_at": "2024-06-01T10:00:00+03:00",
            "author": "я",
            "is_me": True,
            "is_bot": False,
            "workflow_state": None,
        }
    ]
    rec = classify(meta, messages)
    assert "Тестовые" not in rec.categories
    assert rec.test_reasons == []
    assert rec.action == "Ждать ответа HR"
    assert "после теста" not in rec.action_detail
    assert lead_tag(rec) == "wait"
