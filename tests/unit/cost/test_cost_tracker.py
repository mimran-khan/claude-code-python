"""Unit tests for ``claude_code.cost.tracker``."""

from __future__ import annotations

import pytest

from claude_code.cost.tracker import (
    CostTracker,
    ModelUsage,
    StoredCostState,
    format_cost,
    format_total_cost,
)


def test_format_cost_large_values_two_decimals() -> None:
    # ``round(x * 100) / 100`` uses banker's rounding (12.345 -> 12.34).
    assert format_cost(12.345) == "$12.34"
    assert format_cost(0.51) == "$0.51"


def test_format_cost_small_values_respects_decimal_places() -> None:
    assert format_cost(0.05, max_decimal_places=3) == "$0.050"


def test_cost_tracker_add_cost_aggregates_per_model() -> None:
    t = CostTracker()
    t.add_cost(0.01, "m1", input_tokens=10, output_tokens=2)
    t.add_cost(0.02, "m1", cache_read_tokens=3, cache_creation_tokens=1, web_search_requests=2)
    assert t.total_cost_usd == pytest.approx(0.03)
    assert t.total_input_tokens == 10
    assert t.model_usage["m1"].web_search_requests == 2


def test_cost_tracker_lines_and_durations() -> None:
    t = CostTracker()
    t.add_lines_changed(3, 1)
    t.add_api_duration(1000.0, include_retries=True)
    t.add_api_duration(500.0, include_retries=False)
    t.add_tool_duration(200.0)
    t.set_total_duration(5000.0)
    assert t.total_lines_added == 3
    assert t.total_api_duration == 1500.0
    assert t.total_tool_duration == 200.0
    assert t.total_duration == 5000.0


def test_cost_tracker_reset_clears_state() -> None:
    t = CostTracker()
    t.add_cost(1.0, "x")
    t.has_unknown_model_cost = True
    t.reset()
    assert t.total_cost_usd == 0.0
    assert not t.model_usage
    assert t.has_unknown_model_cost is False


def test_to_stored_state_and_restore() -> None:
    t = CostTracker()
    t.add_cost(0.5, "m", input_tokens=1)
    t.add_lines_changed(2, 4)
    state = t.to_stored_state()
    assert isinstance(state, StoredCostState)
    assert state.total_cost_usd == pytest.approx(0.5)

    t2 = CostTracker()
    state.last_duration = 99.0
    t2.restore_from_state(state)
    assert t2.total_cost_usd == pytest.approx(0.5)
    assert t2.total_duration == 99.0
    assert "m" in t2.model_usage


def test_format_total_cost_includes_unknown_model_flag() -> None:
    t = CostTracker()
    t.add_cost(0.1, "m")
    t.set_total_duration(3000.0)
    t.has_unknown_model_cost = True
    out = format_total_cost(t)
    assert "Total cost" in out
    assert "inaccurate" in out
    assert "Usage by model" in out


def test_format_total_cost_empty_model_usage_line() -> None:
    t = CostTracker()
    t.set_total_duration(0.0)
    out = format_total_cost(t)
    assert "0 input" in out


def test_model_usage_dataclass_defaults() -> None:
    u = ModelUsage()
    assert u.input_tokens == 0
    assert u.cost_usd == 0.0
