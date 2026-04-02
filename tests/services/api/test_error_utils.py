"""Tests for services.api.error_utils (TS parity helpers)."""

from __future__ import annotations

import pytest

from claude_code.services.api.error_utils import (
    extract_connection_error_details,
    format_api_error,
    get_ssl_error_hint,
    sanitize_api_error,
)


class _ErrWithCode(Exception):
    def __init__(self, code: str, msg: str = "x") -> None:
        super().__init__(msg)
        self.code = code


def test_extract_connection_error_details_finds_ssl_code() -> None:
    inner = _ErrWithCode("CERT_HAS_EXPIRED", "cert bad")
    outer = RuntimeError("wrap")
    outer.__cause__ = inner
    d = extract_connection_error_details(outer)
    assert d is not None
    assert d.code == "CERT_HAS_EXPIRED"
    assert d.is_ssl_error is True


def test_get_ssl_error_hint() -> None:
    e = _ErrWithCode("UNABLE_TO_VERIFY_LEAF_SIGNATURE")
    hint = get_ssl_error_hint(e)
    assert hint is not None
    assert "NODE_EXTRA_CA_CERTS" in hint


def test_sanitize_api_error_strips_html_title() -> None:
    raw = "<!DOCTYPE html><html><title>Bad Gateway</title></html>"
    assert sanitize_api_error(type("E", (), {"message": raw})()) == "Bad Gateway"


def test_format_api_error_nested_dict_shape() -> None:
    err = {
        "error": {"error": {"message": "nested fail"}},
        "status": 400,
    }
    assert format_api_error(err) == "nested fail"


@pytest.mark.parametrize(
    ("code", "needle"),
    [
        ("ETIMEDOUT", "timed out"),
        ("DEPTH_ZERO_SELF_SIGNED_CERT", "Self-signed"),
    ],
)
def test_format_api_error_ssl_and_timeout(code: str, needle: str) -> None:
    e = _ErrWithCode(code)
    out = format_api_error(e)
    assert needle.lower() in out.lower()
