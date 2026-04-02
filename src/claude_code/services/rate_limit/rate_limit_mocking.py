"""
Facade for applying Ant-only mock rate-limit headers to HTTP responses.

Migrated from: services/rateLimitMocking.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .mock_rate_limits import (
    check_mock_fast_mode_rate_limit,
    get_mock_headerless_429_message,
    get_mock_headers,
    is_mock_fast_mode_rate_limit_scenario,
    should_process_mock_limits,
)


@dataclass
class MockRateLimitAPIError(Exception):
    """HTTP 429 shaped like Anthropic API errors for mock limit testing."""

    status_code: int = 429
    message: str = "Rate limit exceeded"
    body: dict[str, Any] = field(
        default_factory=lambda: {"error": {"type": "rate_limit_error", "message": "Rate limit exceeded"}}
    )
    headers: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


def process_rate_limit_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return headers with mock unified limits merged when /mock-limits is active."""
    if should_process_mock_limits():
        from .mock_rate_limits import apply_mock_headers

        return apply_mock_headers(headers)
    return dict(headers)


def should_process_rate_limits(is_subscriber: bool) -> bool:
    return is_subscriber or should_process_mock_limits()


def check_mock_rate_limit_error(
    current_model: str,
    is_fast_mode_active: bool | None = None,
) -> MockRateLimitAPIError | None:
    """
    If mock limits demand a 429, return a MockRateLimitAPIError; else None.

    Mirrors TypeScript checkMockRateLimitError (APIError with status 429).
    """
    if not should_process_mock_limits():
        return None

    headerless = get_mock_headerless_429_message()
    if headerless:
        return MockRateLimitAPIError(
            message=headerless,
            body={"error": {"type": "rate_limit_error", "message": headerless}},
            headers={},
        )

    mock = get_mock_headers()
    if not mock:
        return None

    status = mock.get("anthropic-ratelimit-unified-status")
    overage_status = mock.get("anthropic-ratelimit-unified-overage-status")
    rate_limit_type = mock.get("anthropic-ratelimit-unified-representative-claim")
    is_opus_limit = rate_limit_type == "seven_day_opus"
    is_using_opus = "opus" in current_model.lower()
    if is_opus_limit and not is_using_opus:
        return None

    if is_mock_fast_mode_rate_limit_scenario():
        fast_headers = check_mock_fast_mode_rate_limit(is_fast_mode_active)
        if fast_headers is None:
            return None
        return MockRateLimitAPIError(headers=dict(fast_headers))

    should_throw = status == "rejected" and (not overage_status or overage_status == "rejected")
    if should_throw:
        return MockRateLimitAPIError(headers=dict(mock))
    return None


def is_mock_rate_limit_error(error: BaseException) -> bool:
    return should_process_mock_limits() and isinstance(error, MockRateLimitAPIError)
