"""Default poll interval config (ported from bridge/pollConfigDefaults.ts)."""

from __future__ import annotations

from dataclasses import dataclass

_POLL_INTERVAL_MS_NOT_AT_CAPACITY = 2000
_POLL_INTERVAL_MS_AT_CAPACITY = 600_000
_MULTISESSION_POLL_INTERVAL_MS_NOT_AT_CAPACITY = _POLL_INTERVAL_MS_NOT_AT_CAPACITY
_MULTISESSION_POLL_INTERVAL_MS_PARTIAL_CAPACITY = _POLL_INTERVAL_MS_NOT_AT_CAPACITY
_MULTISESSION_POLL_INTERVAL_MS_AT_CAPACITY = _POLL_INTERVAL_MS_AT_CAPACITY


@dataclass
class PollIntervalConfig:
    poll_interval_ms_not_at_capacity: int
    poll_interval_ms_at_capacity: int
    non_exclusive_heartbeat_interval_ms: int
    multisession_poll_interval_ms_not_at_capacity: int
    multisession_poll_interval_ms_partial_capacity: int
    multisession_poll_interval_ms_at_capacity: int
    reclaim_older_than_ms: int
    session_keepalive_interval_v2_ms: int


DEFAULT_POLL_CONFIG = PollIntervalConfig(
    poll_interval_ms_not_at_capacity=_POLL_INTERVAL_MS_NOT_AT_CAPACITY,
    poll_interval_ms_at_capacity=_POLL_INTERVAL_MS_AT_CAPACITY,
    non_exclusive_heartbeat_interval_ms=0,
    multisession_poll_interval_ms_not_at_capacity=_MULTISESSION_POLL_INTERVAL_MS_NOT_AT_CAPACITY,
    multisession_poll_interval_ms_partial_capacity=_MULTISESSION_POLL_INTERVAL_MS_PARTIAL_CAPACITY,
    multisession_poll_interval_ms_at_capacity=_MULTISESSION_POLL_INTERVAL_MS_AT_CAPACITY,
    reclaim_older_than_ms=5000,
    session_keepalive_interval_v2_ms=120_000,
)
