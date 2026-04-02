"""Claude AI unified rate limit state (mirrors services/claudeAiLimits.ts core)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Literal

QuotaStatus = Literal["allowed", "allowed_warning", "rejected"]
RateLimitType = Literal[
    "five_hour",
    "seven_day",
    "seven_day_opus",
    "seven_day_sonnet",
    "overage",
]
OverageDisabledReason = Literal[
    "overage_not_provisioned",
    "org_level_disabled",
    "org_level_disabled_until",
    "out_of_credits",
    "seat_tier_level_disabled",
    "member_level_disabled",
    "seat_tier_zero_credit_limit",
    "group_zero_credit_limit",
    "member_zero_credit_limit",
    "org_service_level_disabled",
    "org_service_zero_credit_limit",
    "no_limits_configured",
    "unknown",
]

_RATE_LIMIT_TYPES: frozenset[str] = frozenset(
    ("five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet", "overage")
)
_OVERAGE_REASONS: frozenset[str] = frozenset(
    (
        "overage_not_provisioned",
        "org_level_disabled",
        "org_level_disabled_until",
        "out_of_credits",
        "seat_tier_level_disabled",
        "member_level_disabled",
        "seat_tier_zero_credit_limit",
        "group_zero_credit_limit",
        "member_zero_credit_limit",
        "org_service_level_disabled",
        "org_service_zero_credit_limit",
        "no_limits_configured",
        "unknown",
    )
)


@dataclass
class ClaudeAILimitsState:
    status: QuotaStatus = "allowed"
    unified_rate_limit_fallback_available: bool = False
    resets_at: float | None = None
    rate_limit_type: RateLimitType | None = None
    utilization: float | None = None
    overage_status: QuotaStatus | None = None
    overage_resets_at: float | None = None
    overage_disabled_reason: OverageDisabledReason | None = None
    is_using_overage: bool = False
    surpassed_threshold: int | None = None


@dataclass
class RawWindowUtilization:
    utilization: float
    resets_at: float


@dataclass
class RawUtilization:
    five_hour: RawWindowUtilization | None = None
    seven_day: RawWindowUtilization | None = None


_current = ClaudeAILimitsState()
_raw_utilization = RawUtilization()
_listeners: set[Callable[[ClaudeAILimitsState], None]] = set()

RATE_LIMIT_DISPLAY_NAMES: dict[RateLimitType, str] = {
    "five_hour": "session limit",
    "seven_day": "weekly limit",
    "seven_day_opus": "Opus limit",
    "seven_day_sonnet": "Sonnet limit",
    "overage": "extra usage limit",
}


def get_rate_limit_display_name(limit_type: RateLimitType) -> str:
    return RATE_LIMIT_DISPLAY_NAMES.get(limit_type, str(limit_type))


def current_limits_state() -> ClaudeAILimitsState:
    return replace(_current)


def get_raw_utilization() -> RawUtilization:
    return replace(_raw_utilization)


def set_status_listener(cb: Callable[[ClaudeAILimitsState], None]) -> None:
    _listeners.add(cb)


def emit_status_change(limits: ClaudeAILimitsState) -> None:
    global _current
    _current = limits
    for fn in list(_listeners):
        fn(limits)


def _header_map(headers: dict[str, str] | list[tuple[str, str]]) -> dict[str, str]:
    if isinstance(headers, dict):
        return {k.lower(): v for k, v in headers.items()}
    return {k.lower(): v for k, v in headers}


def _extract_raw(h: dict[str, str]) -> RawUtilization:
    raw = RawUtilization()
    u5, r5 = (
        h.get("anthropic-ratelimit-unified-5h-utilization"),
        h.get("anthropic-ratelimit-unified-5h-reset"),
    )
    if u5 is not None and r5 is not None:
        raw.five_hour = RawWindowUtilization(utilization=float(u5), resets_at=float(r5))
    u7, r7 = (
        h.get("anthropic-ratelimit-unified-7d-utilization"),
        h.get("anthropic-ratelimit-unified-7d-reset"),
    )
    if u7 is not None and r7 is not None:
        raw.seven_day = RawWindowUtilization(utilization=float(u7), resets_at=float(r7))
    return raw


def compute_new_limits_from_headers(
    headers: dict[str, str] | list[tuple[str, str]],
) -> ClaudeAILimitsState:
    h = _header_map(headers)
    status_s = h.get("anthropic-ratelimit-unified-status", "allowed")
    status: QuotaStatus = status_s if status_s in ("allowed", "allowed_warning", "rejected") else "allowed"
    resets_raw = h.get("anthropic-ratelimit-unified-reset")
    resets_at = float(resets_raw) if resets_raw is not None else None
    unified_fb = h.get("anthropic-ratelimit-unified-fallback") == "available"
    rlt_raw = h.get("anthropic-ratelimit-unified-representative-claim")
    rate_limit_type: RateLimitType | None = (
        rlt_raw if rlt_raw in _RATE_LIMIT_TYPES else None  # type: ignore[assignment]
    )
    os_raw = h.get("anthropic-ratelimit-unified-overage-status")
    overage_status: QuotaStatus | None = os_raw if os_raw in ("allowed", "allowed_warning", "rejected") else None
    ort = h.get("anthropic-ratelimit-unified-overage-reset")
    overage_resets_at = float(ort) if ort is not None else None
    odr = h.get("anthropic-ratelimit-unified-overage-disabled-reason")
    overage_disabled_reason: OverageDisabledReason | None = None
    if odr:
        overage_disabled_reason = (
            odr if odr in _OVERAGE_REASONS else "unknown"  # type: ignore[assignment]
        )
    is_using_overage = status == "rejected" and overage_status in (
        "allowed",
        "allowed_warning",
    )
    final_status: QuotaStatus = status
    if status in ("allowed", "allowed_warning"):
        final_status = "allowed"
    return ClaudeAILimitsState(
        status=final_status,
        unified_rate_limit_fallback_available=unified_fb,
        resets_at=resets_at,
        rate_limit_type=rate_limit_type,
        overage_status=overage_status,
        overage_resets_at=overage_resets_at,
        overage_disabled_reason=overage_disabled_reason,
        is_using_overage=is_using_overage,
    )


def extract_quota_status_from_headers(
    headers: dict[str, str] | list[tuple[str, str]],
    *,
    should_process: bool = True,
) -> None:
    global _raw_utilization, _current
    if not should_process:
        _raw_utilization = RawUtilization()
        if _current.status != "allowed" or _current.resets_at is not None:
            emit_status_change(ClaudeAILimitsState())
        return
    h = _header_map(headers)
    _raw_utilization = _extract_raw(h)
    new_limits = compute_new_limits_from_headers(h)
    if new_limits != _current:
        emit_status_change(new_limits)
