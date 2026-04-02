"""
Attach analytics + error log sinks (startup hook).

Migrated from: utils/sinks.ts
"""

from __future__ import annotations

from .error_log_sink import initialize_error_log_sink


def init_sinks() -> None:
    """Initialize error logging first, then analytics (matches TS ordering)."""

    from ..services.analytics.sink import initialize_analytics_sink

    initialize_error_log_sink()
    initialize_analytics_sink()


__all__ = ["init_sinks"]
