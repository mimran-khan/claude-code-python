"""
Centralized rate limit message generation.

Single source of truth for all rate limit-related messages.

Migrated from: services/rateLimitMessages.ts (345 lines)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..utils.format import format_reset_time

FEEDBACK_CHANNEL_ANT = "#briarpatch-cc"

# All possible rate limit error message prefixes
RATE_LIMIT_ERROR_PREFIXES = (
    "You've hit your",
    "You've used",
    "You're now using extra usage",
    "You're close to",
    "You're out of extra usage",
)


def is_rate_limit_error_message(text: str) -> bool:
    """
    Check if a message is a rate limit error.

    Args:
        text: The message text.

    Returns:
        True if this is a rate limit error message.
    """
    return any(text.startswith(prefix) for prefix in RATE_LIMIT_ERROR_PREFIXES)


@dataclass
class RateLimitMessage:
    """A rate limit message with severity."""

    message: str
    severity: Literal["error", "warning"]


@dataclass
class ClaudeAILimits:
    """Rate limit information from the API."""

    status: str = "allowed"
    is_using_overage: bool = False
    overage_status: str | None = None
    overage_disabled_reason: str | None = None
    rate_limit_type: str | None = None
    resets_at: int | None = None
    overage_resets_at: int | None = None
    utilization: float | None = None


def get_rate_limit_message(
    limits: ClaudeAILimits,
    model: str,
) -> RateLimitMessage | None:
    """
    Get the appropriate rate limit message based on limit state.

    Returns None if no message should be shown.

    Args:
        limits: The current rate limits.
        model: The model being used.

    Returns:
        A RateLimitMessage or None.
    """
    # Check overage scenarios first
    if limits.is_using_overage:
        if limits.overage_status == "allowed_warning":
            return RateLimitMessage(
                message="You're close to your extra usage spending limit",
                severity="warning",
            )
        return None

    # ERROR STATES - when limits are rejected
    if limits.status == "rejected":
        return RateLimitMessage(
            message=_get_limit_reached_text(limits, model),
            severity="error",
        )

    # WARNING STATES - when approaching limits
    if limits.status == "allowed_warning":
        WARNING_THRESHOLD = 0.7
        if limits.utilization is not None and limits.utilization < WARNING_THRESHOLD:
            return None

        text = _get_early_warning_text(limits)
        if text:
            return RateLimitMessage(message=text, severity="warning")

    return None


def get_rate_limit_error_message(
    limits: ClaudeAILimits,
    model: str,
) -> str | None:
    """
    Get error message for API errors.

    Returns the message string or None if no error message should be shown.

    Args:
        limits: The current rate limits.
        model: The model being used.

    Returns:
        Error message string or None.
    """
    message = get_rate_limit_message(limits, model)
    if message and message.severity == "error":
        return message.message
    return None


def get_rate_limit_warning(
    limits: ClaudeAILimits,
    model: str,
) -> str | None:
    """
    Get warning message for UI footer.

    Returns the warning message string or None if no warning should be shown.

    Args:
        limits: The current rate limits.
        model: The model being used.

    Returns:
        Warning message string or None.
    """
    message = get_rate_limit_message(limits, model)
    if message and message.severity == "warning":
        return message.message
    return None


def _get_limit_reached_text(limits: ClaudeAILimits, model: str) -> str:
    """Get the error text when limits are reached."""
    reset_time = format_reset_time(limits.resets_at, show_timezone=True) if limits.resets_at else None
    overage_reset_time = (
        format_reset_time(limits.overage_resets_at, show_timezone=True) if limits.overage_resets_at else None
    )
    reset_message = f" · resets {reset_time}" if reset_time else ""

    # If both subscription and overage are exhausted
    if limits.overage_status == "rejected":
        overage_reset_message = ""
        if limits.resets_at and limits.overage_resets_at:
            if limits.resets_at < limits.overage_resets_at:
                overage_reset_message = f" · resets {reset_time}"
            else:
                overage_reset_message = f" · resets {overage_reset_time}"
        elif reset_time:
            overage_reset_message = f" · resets {reset_time}"
        elif overage_reset_time:
            overage_reset_message = f" · resets {overage_reset_time}"

        if limits.overage_disabled_reason == "out_of_credits":
            return f"You're out of extra usage{overage_reset_message}"

        return _format_limit_reached_text("limit", overage_reset_message, model)

    if limits.rate_limit_type == "seven_day_sonnet":
        return _format_limit_reached_text("Sonnet limit", reset_message, model)

    if limits.rate_limit_type == "seven_day_opus":
        return _format_limit_reached_text("Opus limit", reset_message, model)

    if limits.rate_limit_type == "seven_day":
        return _format_limit_reached_text("weekly limit", reset_message, model)

    if limits.rate_limit_type == "five_hour":
        return _format_limit_reached_text("session limit", reset_message, model)

    return _format_limit_reached_text("usage limit", reset_message, model)


def _get_early_warning_text(limits: ClaudeAILimits) -> str | None:
    """Get the warning text when approaching limits."""
    limit_name: str | None = None

    if limits.rate_limit_type == "seven_day":
        limit_name = "weekly limit"
    elif limits.rate_limit_type == "five_hour":
        limit_name = "session limit"
    elif limits.rate_limit_type == "seven_day_opus":
        limit_name = "Opus limit"
    elif limits.rate_limit_type == "seven_day_sonnet":
        limit_name = "Sonnet limit"
    elif limits.rate_limit_type == "overage":
        limit_name = "extra usage"
    else:
        return None

    used = int(limits.utilization * 100) if limits.utilization else None
    reset_time = format_reset_time(limits.resets_at, show_timezone=True) if limits.resets_at else None

    if used and reset_time:
        return f"You've used {used}% of your {limit_name} · resets {reset_time}"

    if used:
        return f"You've used {used}% of your {limit_name}"

    if limits.rate_limit_type == "overage":
        limit_name += " limit"

    if reset_time:
        return f"Approaching {limit_name} · resets {reset_time}"

    return f"Approaching {limit_name}"


def get_using_overage_text(limits: ClaudeAILimits) -> str:
    """
    Get notification text for overage mode transitions.

    Used for transient notifications when entering overage mode.

    Args:
        limits: The current rate limits.

    Returns:
        The overage notification text.
    """
    reset_time = format_reset_time(limits.resets_at, show_timezone=True) if limits.resets_at else ""

    limit_name = ""
    if limits.rate_limit_type == "five_hour":
        limit_name = "session limit"
    elif limits.rate_limit_type == "seven_day":
        limit_name = "weekly limit"
    elif limits.rate_limit_type == "seven_day_opus":
        limit_name = "Opus limit"
    elif limits.rate_limit_type == "seven_day_sonnet":
        limit_name = "Sonnet limit"

    if not limit_name:
        return "Now using extra usage"

    reset_message = f" · Your {limit_name} resets {reset_time}" if reset_time else ""
    return f"You're now using extra usage{reset_message}"


def _format_limit_reached_text(
    limit: str,
    reset_message: str,
    model: str,
) -> str:
    """Format the limit reached error text."""
    import os

    if os.environ.get("USER_TYPE") == "ant":
        return (
            f"You've hit your {limit}{reset_message}. "
            f"If you have feedback about this limit, post in {FEEDBACK_CHANNEL_ANT}. "
            "You can reset your limits with /reset-limits"
        )

    return f"You've hit your {limit}{reset_message}"
