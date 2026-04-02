"""Tests for services.analytics.metadata."""

from __future__ import annotations

import pytest

from claude_code.services.analytics import metadata as md


def test_get_event_metadata_keys() -> None:
    meta = md.get_event_metadata()
    assert "platform" in meta
    assert "python_version" in meta
    assert meta["user_type"] in ("external",) or isinstance(meta["user_type"], str)


def test_enrich_metadata_merges(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_TYPE", "internal")
    base = md.get_event_metadata()
    out = md.enrich_metadata({"feature": "x"}, extra={"n": 1})
    assert out["feature"] == "x"
    assert out["n"] == 1
    assert "platform" in out
    monkeypatch.delenv("USER_TYPE", raising=False)
