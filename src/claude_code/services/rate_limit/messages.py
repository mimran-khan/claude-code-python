"""
Rate Limit Messages.

Centralized rate limit message generation.
Single source of truth for all rate limit-related messages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# All possible rate limit error message prefixes
RATE_LIMIT_ERROR_PREFIXES = (
    "You've hit your",
    "You've used",
    "You're now using extra usage",
    "You're close to",
    "You're out of extra usage",
)


def is_rate_limit_error_message(text: str) -> bool:
    """Check if a message is a rate limit error.

    Args:
        text: The message text to check

    Returns:
        True if the text starts with a rate limit error prefix
    """
    return any(text.startswith(prefix) for prefix in RATE_LIMIT_ERROR_PREFIXES)


@dataclass
class RateLimitMessage:
    """A rate limit message with severity."""

    message: str
    severity: Literal["error", "warning"]


@dataclass
class ClaudeAILimits:
    """Claude AI limits state."""

    status: Literal["allowed", "allowed_warning", "rejected"] = "allowed"
    is_using_overage: bool = False
    overage_status: str | None = None
    utilization: float | None = None
    model_limits: dict[str, float] | None = None
    reset_at: str | None = None


def get_rate_limit_message(
    limits: ClaudeAILimits,
    model: str,
) -> RateLimitMessage | None:
    """Get the appropriate rate limit message based on limit state.

    Args:
        limits: The current limits state
        model: The model being used

    Returns:
        A RateLimitMessage or None if no message should be shown
    """
    # Check overage scenarios first
    if limits.is_using_overage:
        if limits.overage_status == "allowed_warning":
            return RateLimitMessage(
                message="You're close to your extra usage spending limit",
                severity="warning",
            )
        return None

    # Error states - when limits are rejected
    if limits.status == "rejected":
        return RateLimitMessage(
            message=_get_limit_reached_text(limits, model),
            severity="error",
        )

    # Warning states - when approaching limits
    if limits.status == "allowed_warning":
        # Only show warnings when utilization is above threshold (70%)
        WARNING_THRESHOLD = 0.7
        if limits.utilization is not None and limits.utilization < WARNING_THRESHOLD:
            return None

        text = _get_early_warning_text(limits)
        if text:
            return RateLimitMessage(message=text, severity="warning")

    return None


def _get_limit_reached_text(limits: ClaudeAILimits, model: str) -> str:
    """Get text for when limit is reached."""
    reset_info = ""
    if limits.reset_at:
        reset_info = f" Resets at {limits.reset_at}."

    return f"You've hit your usage limit for {model}.{reset_info}"


def _get_early_warning_text(limits: ClaudeAILimits) -> str | None:
    """Get early warning text."""
    if limits.utilization is None:
        return None

    pct = int(limits.utilization * 100)
    return f"You've used {pct}% of your usage limit."
