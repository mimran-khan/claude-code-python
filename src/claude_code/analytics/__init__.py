"""
Analytics Module.

Provides event logging and telemetry services.
"""

from .events import (
    AnalyticsSink,
    attach_analytics_sink,
    log_event,
    log_event_async,
)
from .metadata import (
    EventMetadata,
    sanitize_metadata,
    strip_proto_fields,
)

__all__ = [
    # Events
    "log_event",
    "log_event_async",
    "attach_analytics_sink",
    "AnalyticsSink",
    # Metadata
    "EventMetadata",
    "sanitize_metadata",
    "strip_proto_fields",
]
