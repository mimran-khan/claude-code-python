"""
Cron jitter tuning (``utils/cronJitterConfig.ts`` / ``utils/cronTasks.ts`` defaults).

GrowthBook-backed refresh is not wired in Python; callers receive validated defaults.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CronJitterConfig:
    recurring_frac: float
    recurring_cap_ms: int
    one_shot_max_ms: int
    one_shot_floor_ms: int
    one_shot_minute_mod: int
    recurring_max_age_ms: int


DEFAULT_CRON_JITTER_CONFIG = CronJitterConfig(
    recurring_frac=0.1,
    recurring_cap_ms=15 * 60 * 1000,
    one_shot_max_ms=90 * 1000,
    one_shot_floor_ms=0,
    one_shot_minute_mod=30,
    recurring_max_age_ms=7 * 24 * 60 * 60 * 1000,
)


def get_cron_jitter_config() -> CronJitterConfig:
    """Return jitter configuration (defaults until GrowthBook bridge exists)."""

    return DEFAULT_CRON_JITTER_CONFIG


__all__ = [
    "CronJitterConfig",
    "DEFAULT_CRON_JITTER_CONFIG",
    "get_cron_jitter_config",
]
