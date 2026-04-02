"""
Formatted wall-clock duration since a start timestamp.

Migrated from: hooks/useElapsedTime.ts
"""

from __future__ import annotations

import time

from claude_code.utils.format import format_duration


def format_elapsed_time_ms(
    start_time_ms: float,
    *,
    now_ms: float | None = None,
    paused_ms: float = 0.0,
    end_time_ms: float | None = None,
) -> str:
    """
    Return human-readable duration (e.g. ``1m 23s``) for the active window.

    Args:
        start_time_ms: Unix epoch milliseconds when the timer started.
        now_ms: Current time in ms; defaults to ``time.time() * 1000`` if None.
        paused_ms: Total paused duration to subtract (ms).
        end_time_ms: If set, freeze duration at this timestamp (completed tasks).
    """
    if end_time_ms is not None:
        end = end_time_ms
    elif now_ms is not None:
        end = now_ms
    else:
        end = time.time() * 1000.0
    raw = max(0.0, end - start_time_ms - paused_ms)
    return format_duration(raw)
