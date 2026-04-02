"""
First-party analytics event logger (internal CLI telemetry).

Migrated from: services/analytics/firstPartyEventLogger.ts (subset).
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

import structlog

from .first_party_event_logging_exporter import FirstPartyEventLoggingExporter
from .metadata import enrich_metadata, get_event_metadata
from .sink_killswitch import is_sink_killed

logger = structlog.get_logger(__name__)

_exporter: FirstPartyEventLoggingExporter | None = None
_pending: list[dict[str, Any]] = []


def is_1p_event_logging_enabled() -> bool:
    if is_sink_killed("firstParty"):
        return False
    return os.getenv("CLAUDE_CODE_DISABLE_1P_EVENTS", "").lower() not in ("1", "true", "yes")


def initialize_1p_event_logging() -> None:
    global _exporter
    if not is_1p_event_logging_enabled():
        return
    _exporter = FirstPartyEventLoggingExporter(
        is_killed=lambda: is_sink_killed("firstParty"),
    )


def log_event_to_1p(
    event_name: str,
    metadata: dict[str, bool | int | float | None] | None = None,
) -> None:
    """Queue a structured event for batch export."""
    if not is_1p_event_logging_enabled():
        return
    if is_sink_killed("firstParty"):
        return
    meta = metadata or {}
    base = enrich_metadata(get_event_metadata(), dict(meta))
    record = {
        "event_type": "ClaudeCodeInternalEvent",
        "event_data": {
            "event_name": event_name,
            "event_id": str(uuid.uuid4()),
            "core_metadata": base,
            "event_metadata": meta,
        },
    }
    global _pending, _exporter
    _pending.append(record)
    if _exporter is None:
        initialize_1p_event_logging()
    if _exporter and len(_pending) >= _exporter.max_batch_size:
        batch = _pending
        _pending = []
        _exporter.export_batch(batch)


@dataclass
class GrowthBookExperimentData:
    """Payload for GrowthBook experiment assignment logging."""

    experiment_id: str
    variation_id: int
    user_attributes: dict[str, Any] | None = None
    experiment_metadata: dict[str, Any] | None = None


# Prefixes for very chatty internal events (drop entirely).
_NOISY_EVENT_PREFIXES: tuple[str, ...] = (
    "debug_",
    "tengu_verbose_",
)


def should_sample_event(event_name: str) -> int | None:
    """
    Sampling for high-volume events. Returns 0 to drop, positive int = sample_rate
    metadata, None = no sampling adjustment.
    """
    if event_name.startswith(_NOISY_EVENT_PREFIXES):
        return 0
    return None


def log_growthbook_experiment_to_1p(data: GrowthBookExperimentData) -> None:
    if not is_1p_event_logging_enabled() or is_sink_killed("firstParty"):
        return
    record = {
        "event_type": "GrowthbookExperimentEvent",
        "event_data": {
            "experiment_id": data.experiment_id,
            "variation_id": data.variation_id,
            "user_attributes": data.user_attributes,
            "experiment_metadata": data.experiment_metadata,
            "environment": "production",
        },
    }
    global _pending, _exporter
    _pending.append(record)
    if _exporter is None:
        initialize_1p_event_logging()
