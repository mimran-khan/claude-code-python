"""Tests for bootstrap response parsing."""

from __future__ import annotations

from claude_code.services.api.bootstrap import _parse_bootstrap_response


def test_parse_bootstrap_response_valid() -> None:
    raw = {
        "client_data": {"flag": True},
        "additional_model_options": [
            {"model": "m", "name": "M", "description": "d"},
        ],
    }
    p = _parse_bootstrap_response(raw)
    assert p is not None
    assert p.client_data == {"flag": True}
    assert len(p.additional_model_options) == 1
    assert p.additional_model_options[0].value == "m"


def test_parse_bootstrap_response_rejects_bad_options_type() -> None:
    assert _parse_bootstrap_response({"additional_model_options": "nope"}) is None
