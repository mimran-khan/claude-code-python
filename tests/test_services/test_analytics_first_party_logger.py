"""
Tests for first-party analytics event logging.

Note: ``services/analytics/logger.py`` is not present in this port; coverage targets
``first_party_event_logger.py`` which implements structured event logging.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import claude_code.services.analytics.first_party_event_logger as fpl


@pytest.fixture(autouse=True)
def reset_first_party_state() -> None:
    fpl._pending.clear()
    fpl._exporter = None
    yield
    fpl._pending.clear()
    fpl._exporter = None


def test_is_1p_event_logging_disabled_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_1P_EVENTS", "true")
    with patch.object(fpl, "is_sink_killed", return_value=False):
        assert fpl.is_1p_event_logging_enabled() is False


def test_is_1p_event_logging_disabled_when_sink_killed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_DISABLE_1P_EVENTS", raising=False)
    with patch.object(fpl, "is_sink_killed", return_value=True):
        assert fpl.is_1p_event_logging_enabled() is False


def test_initialize_1p_skips_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_1P_EVENTS", "1")
    with patch.object(fpl, "is_sink_killed", return_value=False):
        fpl.initialize_1p_event_logging()
    assert fpl._exporter is None


def test_log_event_to_1p_skips_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_1P_EVENTS", "yes")
    with patch.object(fpl, "is_sink_killed", return_value=False):
        fpl.log_event_to_1p("evt", {"k": 1})
    assert fpl._pending == []


def test_log_event_to_1p_skips_when_sink_killed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_DISABLE_1P_EVENTS", raising=False)
    with patch.object(fpl, "is_sink_killed", return_value=True):
        fpl.log_event_to_1p("evt")
    assert fpl._pending == []


def test_log_event_to_1p_queues_record(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_DISABLE_1P_EVENTS", raising=False)
    with patch.object(fpl, "is_sink_killed", return_value=False):
        with patch.object(fpl, "enrich_metadata", side_effect=lambda m, x: {**m, **x}):
            with patch.object(fpl, "get_event_metadata", return_value={"session": "s"}):
                fpl.log_event_to_1p("my_event", {"n": 42})
    assert len(fpl._pending) == 1
    rec = fpl._pending[0]
    assert rec["event_type"] == "ClaudeCodeInternalEvent"
    assert rec["event_data"]["event_name"] == "my_event"
    assert rec["event_data"]["event_metadata"]["n"] == 42


def test_should_sample_event_drops_noisy_prefixes() -> None:
    assert fpl.should_sample_event("debug_foo") == 0
    assert fpl.should_sample_event("tengu_verbose_x") == 0


def test_should_sample_event_normal_returns_none() -> None:
    assert fpl.should_sample_event("tool_used") is None


def test_log_growthbook_skips_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_1P_EVENTS", "true")
    data = fpl.GrowthBookExperimentData("exp1", 1)
    with patch.object(fpl, "is_sink_killed", return_value=False):
        fpl.log_growthbook_experiment_to_1p(data)
    assert fpl._pending == []


def test_log_growthbook_queues(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_DISABLE_1P_EVENTS", raising=False)
    data = fpl.GrowthBookExperimentData("exp_z", 2, user_attributes={"a": 1})
    with patch.object(fpl, "is_sink_killed", return_value=False):
        fpl.log_growthbook_experiment_to_1p(data)
    assert len(fpl._pending) == 1
    assert fpl._pending[0]["event_type"] == "GrowthbookExperimentEvent"


def test_log_event_triggers_export_at_batch_size(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_DISABLE_1P_EVENTS", raising=False)
    mock_exporter = MagicMock()
    mock_exporter.max_batch_size = 2
    mock_exporter.export_batch = MagicMock()

    with patch.object(fpl, "is_sink_killed", return_value=False):
        with patch.object(fpl, "enrich_metadata", side_effect=lambda m, x: m):
            with patch.object(fpl, "get_event_metadata", return_value={}):
                fpl._exporter = mock_exporter
                fpl.log_event_to_1p("e1")
                assert len(fpl._pending) == 1
                fpl.log_event_to_1p("e2")

    mock_exporter.export_batch.assert_called_once()
    assert fpl._pending == []
