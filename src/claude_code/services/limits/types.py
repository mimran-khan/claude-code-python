"""
Rate Limit Types.

Type definitions for rate limiting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

QuotaStatus = Literal["allowed", "allowed_warning", "rejected"]

RateLimitType = Literal[
    "five_hour",
    "seven_day",
    "seven_day_opus",
    "seven_day_sonnet",
    "overage",
]


@dataclass
class EarlyWarningThreshold:
    """Threshold for early warning."""

    utilization: float  # 0-1 scale
    time_pct: float  # 0-1 scale


@dataclass
class EarlyWarningConfig:
    """Configuration for early warning."""

    rate_limit_type: RateLimitType
    claim_abbrev: str
    window_seconds: int
    thresholds: list[EarlyWarningThreshold] = field(default_factory=list)


# Early warning configurations in priority order
EARLY_WARNING_CONFIGS: list[EarlyWarningConfig] = [
    EarlyWarningConfig(
        rate_limit_type="five_hour",
        claim_abbrev="5h",
        window_seconds=5 * 60 * 60,
        thresholds=[EarlyWarningThreshold(utilization=0.9, time_pct=0.72)],
    ),
    EarlyWarningConfig(
        rate_limit_type="seven_day",
        claim_abbrev="7d",
        window_seconds=7 * 24 * 60 * 60,
        thresholds=[
            EarlyWarningThreshold(utilization=0.75, time_pct=0.6),
            EarlyWarningThreshold(utilization=0.5, time_pct=0.35),
            EarlyWarningThreshold(utilization=0.25, time_pct=0.15),
        ],
    ),
]


RATE_LIMIT_DISPLAY_NAMES: dict[RateLimitType, str] = {
    "five_hour": "session limit",
    "seven_day": "weekly limit",
    "seven_day_opus": "Opus weekly limit",
    "seven_day_sonnet": "Sonnet weekly limit",
    "overage": "overage limit",
}


@dataclass
class RateLimitInfo:
    """Information about a specific rate limit."""

    limit: int = 0
    remaining: int = 0
    reset_at: str | None = None
    utilization: float = 0.0


@dataclass
class ClaudeAILimits:
    """Current Claude AI limits state."""

    five_hour: RateLimitInfo = field(default_factory=RateLimitInfo)
    seven_day: RateLimitInfo = field(default_factory=RateLimitInfo)
    seven_day_opus: RateLimitInfo = field(default_factory=RateLimitInfo)
    seven_day_sonnet: RateLimitInfo = field(default_factory=RateLimitInfo)
    overage: RateLimitInfo = field(default_factory=RateLimitInfo)

    quota_status: QuotaStatus = "allowed"
    active_limit_type: RateLimitType | None = None
    warning_message: str | None = None
    error_message: str | None = None
