"""
Rate Limit Services.

Provides rate limit message generation and utilities.
"""

from .messages import (
    RATE_LIMIT_ERROR_PREFIXES,
    RateLimitMessage,
    get_rate_limit_message,
    is_rate_limit_error_message,
)
from .mock_rate_limits import (
    MockScenario,
    apply_mock_headers,
    clear_mock_headers,
    get_current_mock_scenario,
    get_mock_headers,
    get_mock_status,
    get_scenario_description,
    reset_mock_rate_limits_state_for_tests,
    set_mock_rate_limit_scenario,
    should_process_mock_limits,
)
from .rate_limit_mocking import (
    MockRateLimitAPIError,
    check_mock_rate_limit_error,
    is_mock_rate_limit_error,
    process_rate_limit_headers,
    should_process_rate_limits,
)

__all__ = [
    "RATE_LIMIT_ERROR_PREFIXES",
    "RateLimitMessage",
    "is_rate_limit_error_message",
    "get_rate_limit_message",
    # Mock limits (Ant-only; mockRateLimits.ts / rateLimitMocking.ts)
    "MockScenario",
    "apply_mock_headers",
    "clear_mock_headers",
    "get_current_mock_scenario",
    "get_mock_headers",
    "get_mock_status",
    "get_scenario_description",
    "reset_mock_rate_limits_state_for_tests",
    "set_mock_rate_limit_scenario",
    "should_process_mock_limits",
    "MockRateLimitAPIError",
    "check_mock_rate_limit_error",
    "is_mock_rate_limit_error",
    "process_rate_limit_headers",
    "should_process_rate_limits",
]
