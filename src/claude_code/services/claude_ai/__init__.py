"""
Claude.ai subscriber limits and quota header parsing.

Migrated from: services/claudeAiLimits.ts (types + header logic; hooks omitted).
"""

from .limits import (
    ClaudeAILimitsState,
    OverageDisabledReason,
    QuotaStatus,
    RateLimitType,
    compute_new_limits_from_headers,
    current_limits_state,
    emit_status_change,
    extract_quota_status_from_headers,
    get_rate_limit_display_name,
    get_raw_utilization,
    set_status_listener,
)
from .limits_hook import (
    add_limits_listener,
    get_current_limits,
    remove_limits_listener,
)

__all__ = [
    "ClaudeAILimitsState",
    "OverageDisabledReason",
    "QuotaStatus",
    "RateLimitType",
    "compute_new_limits_from_headers",
    "current_limits_state",
    "emit_status_change",
    "extract_quota_status_from_headers",
    "get_raw_utilization",
    "get_rate_limit_display_name",
    "set_status_listener",
    "add_limits_listener",
    "remove_limits_listener",
    "get_current_limits",
]
