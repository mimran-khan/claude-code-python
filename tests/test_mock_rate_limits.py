"""Tests for Ant-only mock unified rate limits (mockRateLimits.ts / rateLimitMocking.ts)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from claude_code.services.rate_limit.mock_rate_limits import (
    apply_mock_headers,
    clear_mock_headers,
    get_current_mock_scenario,
    get_mock_headers,
    reset_mock_rate_limits_state_for_tests,
    set_mock_rate_limit_scenario,
    should_process_mock_limits,
)
from claude_code.services.rate_limit.rate_limit_mocking import (
    check_mock_rate_limit_error,
    process_rate_limit_headers,
    should_process_rate_limits,
)


@pytest.fixture(autouse=True)
def _ant_env() -> None:
    with patch.dict(os.environ, {"USER_TYPE": "ant"}, clear=False):
        yield
    reset_mock_rate_limits_state_for_tests()


def test_should_process_mock_limits_false_when_not_ant() -> None:
    reset_mock_rate_limits_state_for_tests()
    with patch.dict(os.environ, {"USER_TYPE": "external"}, clear=False):
        set_mock_rate_limit_scenario("normal")
        assert should_process_mock_limits() is False


def test_normal_scenario_sets_allowed_status() -> None:
    set_mock_rate_limit_scenario("normal")
    h = get_mock_headers()
    assert h is not None
    assert h.get("anthropic-ratelimit-unified-status") == "allowed"


def test_apply_mock_headers_merges() -> None:
    set_mock_rate_limit_scenario("normal")
    merged = apply_mock_headers({"x-custom": "1"})
    assert merged["x-custom"] == "1"
    assert merged.get("anthropic-ratelimit-unified-status") == "allowed"


def test_process_rate_limit_headers() -> None:
    set_mock_rate_limit_scenario("weekly-limit-reached")
    out = process_rate_limit_headers({})
    assert out.get("anthropic-ratelimit-unified-status") == "rejected"


def test_should_process_rate_limits_non_subscriber_with_mock() -> None:
    set_mock_rate_limit_scenario("normal")
    assert should_process_rate_limits(is_subscriber=False) is True


def test_get_current_mock_scenario_weekly() -> None:
    set_mock_rate_limit_scenario("weekly-limit-reached")
    assert get_current_mock_scenario() == "weekly-limit-reached"


def test_check_mock_rate_limit_error_rejects_when_headers_rejected() -> None:
    set_mock_rate_limit_scenario("weekly-limit-reached")
    err = check_mock_rate_limit_error("claude-sonnet-4")
    assert err is not None
    assert err.status_code == 429


def test_opus_limit_skips_when_model_not_opus() -> None:
    set_mock_rate_limit_scenario("opus-limit")
    assert check_mock_rate_limit_error("claude-sonnet-4") is None


def test_clear_mock_headers_disables() -> None:
    set_mock_rate_limit_scenario("normal")
    clear_mock_headers()
    assert get_mock_headers() is None
