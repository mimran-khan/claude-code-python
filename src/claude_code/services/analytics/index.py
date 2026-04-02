"""
Analytics public API (parity with services/analytics/index.ts).

Thin re-export over :mod:`events` so imports match the TypeScript layout.
"""

from __future__ import annotations

from .events import (
    AnalyticsSink,
    attach_analytics_sink,
    log_event,
    log_event_async,
    reset_for_testing,
    strip_proto_fields,
)

__all__ = [
    "AnalyticsSink",
    "attach_analytics_sink",
    "log_event",
    "log_event_async",
    "reset_for_testing",
    "strip_proto_fields",
]
