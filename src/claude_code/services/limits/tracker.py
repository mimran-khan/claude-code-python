"""
Rate Limit Tracker.

Tracks and manages rate limit state.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable

from .types import (
    RATE_LIMIT_DISPLAY_NAMES,
    ClaudeAILimits,
    RateLimitInfo,
    RateLimitType,
)

# Global state
_current_limits = ClaudeAILimits()
_listeners: set[Callable[[ClaudeAILimits], None]] = set()


def get_current_limits() -> ClaudeAILimits:
    """Get the current rate limits.

    Returns:
        Current limits state
    """
    return _current_limits


def update_limits(limits: ClaudeAILimits) -> None:
    """Update the current limits.

    Args:
        limits: New limits state
    """
    global _current_limits
    _current_limits = limits

    # Notify listeners
    for listener in _listeners:
        with contextlib.suppress(Exception):
            listener(limits)


def add_limits_listener(listener: Callable[[ClaudeAILimits], None]) -> None:
    """Add a listener for limits changes.

    Args:
        listener: The callback function
    """
    _listeners.add(listener)


def remove_limits_listener(listener: Callable[[ClaudeAILimits], None]) -> None:
    """Remove a limits listener.

    Args:
        listener: The callback to remove
    """
    _listeners.discard(listener)


def is_rate_limited() -> bool:
    """Check if currently rate limited.

    Returns:
        True if rate limited
    """
    return _current_limits.quota_status == "rejected"


def is_warning() -> bool:
    """Check if in warning state.

    Returns:
        True if approaching limit
    """
    return _current_limits.quota_status == "allowed_warning"


def get_rate_limit_warning() -> str | None:
    """Get the current rate limit warning message.

    Returns:
        Warning message or None
    """
    return _current_limits.warning_message


def get_rate_limit_error() -> str | None:
    """Get the current rate limit error message.

    Returns:
        Error message or None
    """
    return _current_limits.error_message


def get_active_limit_display_name() -> str | None:
    """Get the display name for the active limit.

    Returns:
        Display name or None
    """
    if _current_limits.active_limit_type:
        return RATE_LIMIT_DISPLAY_NAMES.get(_current_limits.active_limit_type)
    return None


def update_from_headers(headers: dict[str, str]) -> None:
    """Update limits from API response headers.

    Args:
        headers: Response headers
    """
    # Parse rate limit headers
    # Header format: x-ratelimit-limit-*, x-ratelimit-remaining-*, x-ratelimit-reset-*

    limit_types: list[tuple[RateLimitType, str]] = [
        ("five_hour", "5h"),
        ("seven_day", "7d"),
        ("seven_day_opus", "7d-opus"),
        ("seven_day_sonnet", "7d-sonnet"),
        ("overage", "overage"),
    ]

    new_limits = ClaudeAILimits()

    for limit_type, header_suffix in limit_types:
        limit = int(headers.get(f"x-ratelimit-limit-{header_suffix}", "0"))
        remaining = int(headers.get(f"x-ratelimit-remaining-{header_suffix}", "0"))
        reset_at = headers.get(f"x-ratelimit-reset-{header_suffix}")

        utilization = 1 - remaining / limit if limit > 0 else 0.0

        info = RateLimitInfo(
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            utilization=utilization,
        )

        setattr(new_limits, limit_type.replace("-", "_"), info)

    update_limits(new_limits)
