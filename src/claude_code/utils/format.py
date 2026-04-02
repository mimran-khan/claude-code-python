"""
Formatting utilities.

Functions for formatting numbers, durations, file sizes, etc.

Migrated from: utils/format.ts (309 lines)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal


def format_file_size(size_in_bytes: int) -> str:
    """
    Format a byte count to a human-readable string.

    Examples:
        format_file_size(1536) → "1.5KB"
        format_file_size(1048576) → "1MB"
    """
    kb = size_in_bytes / 1024

    if kb < 1:
        return f"{size_in_bytes} bytes"

    if kb < 1024:
        formatted = f"{kb:.1f}".rstrip("0").rstrip(".")
        return f"{formatted}KB"

    mb = kb / 1024
    if mb < 1024:
        formatted = f"{mb:.1f}".rstrip("0").rstrip(".")
        return f"{formatted}MB"

    gb = mb / 1024
    formatted = f"{gb:.1f}".rstrip("0").rstrip(".")
    return f"{formatted}GB"


def format_seconds_short(ms: float) -> str:
    """
    Format milliseconds as seconds with 1 decimal place.

    Always keeps the decimal for sub-minute timings.
    """
    return f"{ms / 1000:.1f}s"


def format_duration(
    ms: float,
    *,
    hide_trailing_zeros: bool = False,
    most_significant_only: bool = False,
) -> str:
    """
    Format a duration in milliseconds to a human-readable string.

    Args:
        ms: Duration in milliseconds
        hide_trailing_zeros: Don't show zero components at the end
        most_significant_only: Only show the largest unit

    Returns:
        Formatted duration string (e.g., "1h 30m 45s")
    """
    if ms < 60000:  # Less than 1 minute
        if ms == 0:
            return "0s"
        if ms < 1:
            return f"{ms / 1000:.1f}s"
        s = int(ms // 1000)
        return f"{s}s"

    days = int(ms // 86400000)
    hours = int((ms % 86400000) // 3600000)
    minutes = int((ms % 3600000) // 60000)
    seconds = round((ms % 60000) / 1000)

    # Handle rounding carry-over
    if seconds == 60:
        seconds = 0
        minutes += 1
    if minutes == 60:
        minutes = 0
        hours += 1
    if hours == 24:
        hours = 0
        days += 1

    if most_significant_only:
        if days > 0:
            return f"{days}d"
        if hours > 0:
            return f"{hours}h"
        if minutes > 0:
            return f"{minutes}m"
        return f"{seconds}s"

    if days > 0:
        if hide_trailing_zeros and hours == 0 and minutes == 0:
            return f"{days}d"
        if hide_trailing_zeros and minutes == 0:
            return f"{days}d {hours}h"
        return f"{days}d {hours}h {minutes}m"

    if hours > 0:
        if hide_trailing_zeros and minutes == 0 and seconds == 0:
            return f"{hours}h"
        if hide_trailing_zeros and seconds == 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h {minutes}m {seconds}s"

    if minutes > 0:
        if hide_trailing_zeros and seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {seconds}s"

    return f"{seconds}s"


def format_number(number: float) -> str:
    """
    Format a number in compact notation.

    Examples:
        format_number(1321) → "1.3k"
        format_number(900) → "900"
    """
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}b".rstrip("0").rstrip(".").replace(".0", "")
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}m".rstrip("0").rstrip(".").replace(".0", "")
    if number >= 1000:
        return f"{number / 1000:.1f}k".rstrip("0").rstrip(".").replace(".0", "")

    return str(int(number)) if number == int(number) else f"{number:.1f}"


def format_tokens(count: int) -> str:
    """Format a token count."""
    return format_number(count).replace(".0", "")


RelativeTimeStyle = Literal["long", "short", "narrow"]


def format_relative_time(
    date: datetime,
    *,
    style: RelativeTimeStyle = "narrow",
    numeric: Literal["always", "auto"] = "always",
    now: datetime | None = None,
) -> str:
    """
    Format a datetime as a relative time string.

    Args:
        date: The datetime to format
        style: Output style (long, short, narrow)
        numeric: Whether to always use numeric values
        now: Reference time (defaults to current time)

    Returns:
        Relative time string (e.g., "2h ago", "in 3 days")
    """
    if now is None:
        now = datetime.now(UTC)

    # Ensure both datetimes are timezone-aware
    if date.tzinfo is None:
        date = date.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    diff = date - now
    total_seconds = diff.total_seconds()

    # Determine unit and value
    abs_seconds = abs(total_seconds)

    if abs_seconds < 60:
        value = int(abs_seconds)
        unit = "second"
    elif abs_seconds < 3600:
        value = int(abs_seconds // 60)
        unit = "minute"
    elif abs_seconds < 86400:
        value = int(abs_seconds // 3600)
        unit = "hour"
    elif abs_seconds < 604800:
        value = int(abs_seconds // 86400)
        unit = "day"
    elif abs_seconds < 2592000:
        value = int(abs_seconds // 604800)
        unit = "week"
    elif abs_seconds < 31536000:
        value = int(abs_seconds // 2592000)
        unit = "month"
    else:
        value = int(abs_seconds // 31536000)
        unit = "year"

    # Format based on style
    if style == "narrow":
        unit_abbrev = {
            "second": "s",
            "minute": "m",
            "hour": "h",
            "day": "d",
            "week": "w",
            "month": "mo",
            "year": "y",
        }
        unit_str = unit_abbrev[unit]
    elif style == "short":
        unit_abbrev = {
            "second": "sec",
            "minute": "min",
            "hour": "hr",
            "day": "day",
            "week": "wk",
            "month": "mo",
            "year": "yr",
        }
        unit_str = unit_abbrev[unit]
        if value != 1:
            unit_str += "s" if unit not in ("month", "year") else ""
    else:  # long
        unit_str = unit
        if value != 1:
            unit_str += "s"

    if total_seconds < 0:
        if style == "narrow":
            return f"{value}{unit_str} ago"
        return f"{value} {unit_str} ago"
    else:
        if style == "narrow":
            return f"in {value}{unit_str}"
        return f"in {value} {unit_str}"


def format_date(
    date: datetime,
    *,
    include_time: bool = False,
    include_seconds: bool = False,
) -> str:
    """
    Format a datetime for display.

    Args:
        date: The datetime to format
        include_time: Include time in the output
        include_seconds: Include seconds in the time

    Returns:
        Formatted date string
    """
    if include_time:
        if include_seconds:
            return date.strftime("%Y-%m-%d %H:%M:%S")
        return date.strftime("%Y-%m-%d %H:%M")
    return date.strftime("%Y-%m-%d")


def format_cost(cost_usd: float) -> str:
    """
    Format a cost in USD.

    Examples:
        format_cost(0.001) → "$0.001"
        format_cost(1.5) → "$1.50"
    """
    if cost_usd < 0.01:
        return f"${cost_usd:.4f}".rstrip("0").rstrip(".")
    if cost_usd < 1:
        return f"${cost_usd:.3f}".rstrip("0").rstrip(".")
    return f"${cost_usd:.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a value as a percentage."""
    return f"{value * 100:.{decimals}f}%"


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Adds a suffix if truncated.
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """
    Return singular or plural form based on count.

    Args:
        count: The count
        singular: Singular form
        plural: Plural form (defaults to singular + "s")

    Returns:
        The appropriate form with count prefix
    """
    if plural is None:
        plural = singular + "s"

    form = singular if count == 1 else plural
    return f"{count} {form}"


def format_reset_time(
    reset_time: datetime | None,
    *,
    show_timezone: bool = False,
) -> str:
    """
    Format a reset time for display.

    Args:
        reset_time: The reset datetime
        show_timezone: Include timezone in output

    Returns:
        Formatted reset time string
    """
    if reset_time is None:
        return "unknown"

    if show_timezone:
        return reset_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    return reset_time.strftime("%Y-%m-%d %H:%M:%S")
