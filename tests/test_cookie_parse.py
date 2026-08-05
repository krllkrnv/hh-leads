"""Тесты разбора cookie-дампов разных форматов."""

from __future__ import annotations

from hh_leads.hh_client import cookie_value, normalize_cookie, parse_cookie_map, suggest_hh_host_from_cookie


def test_normalize_classic_header() -> None:
    raw = "hhtoken=abc123; _xsrf=def456; hhuid=xyz"
    assert cookie_value(normalize_cookie(raw), "hhtoken") == "abc123"
    assert cookie_value(normalize_cookie(raw), "_xsrf") == "def456"


def test_normalize_tab_table() -> None:
    raw = (
        'hhtoken\t"example_hhtoken_value"\n'
        '_xsrf\t"example_xsrf_value"\n'
        'hhrole\t"applicant"\n'
    )
    mapped = parse_cookie_map(raw)
    assert mapped["hhtoken"] == "example_hhtoken_value"
    assert mapped["_xsrf"] == "example_xsrf_value"
    normalized = normalize_cookie(raw)
    assert "hhtoken=example_hhtoken_value" in normalized
    assert "_xsrf=example_xsrf_value" in normalized


def test_normalize_storage_blocks() -> None:
    raw = """
__ddg1_
domain	".hh.ru"
path	"/"
value	"ignore-me"
hhtoken
domain	".hh.ru"
path	"/"
value	"tok123"
_xsrf
domain	".hh.ru"
value	"xsrf456"
redirect_host	"example.hh.ru"
"""
    mapped = parse_cookie_map(raw)
    assert mapped["hhtoken"] == "tok123"
    assert mapped["_xsrf"] == "xsrf456"
    assert suggest_hh_host_from_cookie(raw) == "https://example.hh.ru"


def test_normalize_devtools_request_cookies_json() -> None:
    raw = """
    {
      "Request Cookies": {
        "__ddg1_": "noise",
        "hhtoken": "json_tok_abc",
        "_xsrf": "json_xsrf_def",
        "hhuid": "uid--",
        "hhrole": "applicant",
        "redirect_host": "spb.hh.ru",
        "filters1": "{\\"showFilters\\":false}"
      }
    }
    """
    mapped = parse_cookie_map(raw)
    assert mapped["hhtoken"] == "json_tok_abc"
    assert mapped["_xsrf"] == "json_xsrf_def"
    assert mapped["redirect_host"] == "spb.hh.ru"
    normalized = normalize_cookie(raw)
    assert "hhtoken=json_tok_abc" in normalized
    assert "_xsrf=json_xsrf_def" in normalized
    assert suggest_hh_host_from_cookie(raw) == "https://spb.hh.ru"


def test_normalize_flat_cookie_json() -> None:
    raw = '{"hhtoken": "flat_tok", "_xsrf": "flat_xsrf"}'
    mapped = parse_cookie_map(raw)
    assert mapped["hhtoken"] == "flat_tok"
    assert mapped["_xsrf"] == "flat_xsrf"
