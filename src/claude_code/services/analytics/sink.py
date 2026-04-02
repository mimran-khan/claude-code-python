"""
Analytics sink implementation: routes to Datadog and first-party logging.

Migrated from: services/analytics/sink.ts
"""

from __future__ import annotations

from typing import Any

from .datadog import track_datadog_event
from .events import attach_analytics_sink, strip_proto_fields
from .first_party_event_logger import log_event_to_1p, should_sample_event
from .growthbook import check_statsig_feature_gate_cached_may_be_stale
from .sink_killswitch import is_sink_killed

LogEventMetadata = dict[str, Any]

_DATADOG_GATE_NAME = "tengu_log_datadog_events"
_is_datadog_gate_enabled: bool | None = None


def should_track_datadog() -> bool:
    if is_sink_killed("datadog"):
        return False
    if _is_datadog_gate_enabled is not None:
        return _is_datadog_gate_enabled
    return check_statsig_feature_gate_cached_may_be_stale(_DATADOG_GATE_NAME)


def log_event_impl(event_name: str, metadata: LogEventMetadata) -> None:
    sample_result = should_sample_event(event_name)
    if sample_result == 0:
        return
    meta = {**metadata, "sample_rate": sample_result} if sample_result is not None else metadata
    if should_track_datadog():
        track_datadog_event(event_name, strip_proto_fields(dict(meta)))
    log_event_to_1p(event_name, meta)


async def log_event_async_impl(event_name: str, metadata: LogEventMetadata) -> None:
    log_event_impl(event_name, metadata)


class _DefaultAnalyticsSink:
    def log_event(self, event_name: str, metadata: LogEventMetadata) -> None:
        log_event_impl(event_name, metadata)

    async def log_event_async(self, event_name: str, metadata: LogEventMetadata) -> None:
        await log_event_async_impl(event_name, metadata)


def initialize_analytics_gates() -> None:
    global _is_datadog_gate_enabled
    _is_datadog_gate_enabled = check_statsig_feature_gate_cached_may_be_stale(
        _DATADOG_GATE_NAME,
    )


def initialize_analytics_sink() -> None:
    attach_analytics_sink(_DefaultAnalyticsSink())
