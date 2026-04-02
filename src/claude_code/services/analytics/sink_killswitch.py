"""
Per-sink analytics killswitch from GrowthBook dynamic config.

Migrated from: services/analytics/sinkKillswitch.ts
"""

from __future__ import annotations

from typing import Literal

from .growthbook import get_dynamic_config_cached_may_be_stale

SinkName = Literal["datadog", "firstParty"]

_SINK_KILLSWITCH_CONFIG_NAME = "tengu_frond_boric"


def is_sink_killed(sink: SinkName) -> bool:
    """
    Return True when GrowthBook disables dispatch to the named sink.

    Must not be called from inside is_1p_event_logging_enabled (recursion).
    """
    config = get_dynamic_config_cached_may_be_stale(
        _SINK_KILLSWITCH_CONFIG_NAME,
        {},
    )
    if not isinstance(config, dict):
        return False
    val = config.get(sink)
    return val is True
