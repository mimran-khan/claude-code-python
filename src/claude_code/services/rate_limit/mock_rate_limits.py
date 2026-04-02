"""
Ant-only mock unified rate-limit headers for integration testing.

Migrated from: services/mockRateLimits.ts

⚠️ For internal testing only. Headers may not match production API exactly.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from claude_code.utils.billing import set_mock_billing_access_override

from ..oauth.types import SubscriptionType

MockHeaderKey = Literal[
    "status",
    "reset",
    "claim",
    "overage-status",
    "overage-reset",
    "overage-disabled-reason",
    "fallback",
    "fallback-percentage",
    "retry-after",
    "5h-utilization",
    "5h-reset",
    "5h-surpassed-threshold",
    "7d-utilization",
    "7d-reset",
    "7d-surpassed-threshold",
]

MockScenario = Literal[
    "normal",
    "session-limit-reached",
    "approaching-weekly-limit",
    "weekly-limit-reached",
    "overage-active",
    "overage-warning",
    "overage-exhausted",
    "out-of-credits",
    "org-zero-credit-limit",
    "org-spend-cap-hit",
    "member-zero-credit-limit",
    "seat-tier-zero-credit-limit",
    "opus-limit",
    "opus-warning",
    "sonnet-limit",
    "sonnet-warning",
    "fast-mode-limit",
    "fast-mode-short-limit",
    "extra-usage-required",
    "clear",
]

MockHeaders = dict[str, str]

ExceededLimitType = Literal[
    "five_hour",
    "seven_day",
    "seven_day_opus",
    "seven_day_sonnet",
]


@dataclass
class _ExceededLimit:
    type: ExceededLimitType
    resets_at: int


_mock_headers: MockHeaders = {}
_mock_enabled = False
_mock_headerless_429_message: str | None = None
_mock_subscription_type: SubscriptionType = None
_mock_fast_mode_duration_ms: int | None = None
_mock_fast_mode_expires_at: float | None = None
_exceeded_limits: list[_ExceededLimit] = []

DEFAULT_MOCK_SUBSCRIPTION: SubscriptionType = "max"

_VALID_CLAIMS: frozenset[str] = frozenset({"five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet"})


def _is_ant() -> bool:
    return os.environ.get("USER_TYPE") == "ant"


def _end_of_next_month_start_unix() -> int:
    """First moment of next calendar month (UTC), matching TS setMonth(+1, 1) intent."""
    now = datetime.now(UTC)
    y, m = now.year, now.month
    nxt = datetime(y + 1, 1, 1, tzinfo=UTC) if m == 12 else datetime(y, m + 1, 1, tzinfo=UTC)
    return int(nxt.timestamp())


def _update_retry_after() -> None:
    status = _mock_headers.get("anthropic-ratelimit-unified-status")
    overage_status = _mock_headers.get("anthropic-ratelimit-unified-overage-status")
    reset = _mock_headers.get("anthropic-ratelimit-unified-reset")
    if status == "rejected" and (not overage_status or overage_status == "rejected") and reset:
        try:
            reset_ts = int(reset)
        except ValueError:
            _mock_headers.pop("retry-after", None)
            return
        now = int(time.time())
        _mock_headers["retry-after"] = str(max(0, reset_ts - now))
    else:
        _mock_headers.pop("retry-after", None)


def _update_representative_claim() -> None:
    global _mock_headers
    if not _exceeded_limits:
        _mock_headers.pop("anthropic-ratelimit-unified-representative-claim", None)
        _mock_headers.pop("anthropic-ratelimit-unified-reset", None)
        _mock_headers.pop("retry-after", None)
        return

    furthest = max(_exceeded_limits, key=lambda x: x.resets_at)
    _mock_headers["anthropic-ratelimit-unified-representative-claim"] = furthest.type
    _mock_headers["anthropic-ratelimit-unified-reset"] = str(furthest.resets_at)

    if _mock_headers.get("anthropic-ratelimit-unified-status") == "rejected":
        overage_status = _mock_headers.get("anthropic-ratelimit-unified-overage-status")
        if not overage_status or overage_status == "rejected":
            now = int(time.time())
            _mock_headers["retry-after"] = str(max(0, furthest.resets_at - now))
        else:
            _mock_headers.pop("retry-after", None)
    else:
        _mock_headers.pop("retry-after", None)


def set_mock_header(key: MockHeaderKey, value: str | None) -> None:
    """Toggle a single mock header (Ant-only)."""
    global _mock_headers, _mock_enabled, _exceeded_limits
    if not _is_ant():
        return

    _mock_enabled = True

    full_key = "retry-after" if key == "retry-after" else f"anthropic-ratelimit-unified-{key}"

    if value is None or value == "clear":
        _mock_headers.pop(full_key, None)
        if key == "claim":
            _exceeded_limits.clear()
        if key in ("status", "overage-status"):
            _update_retry_after()
        if not _mock_headers:
            _mock_enabled = False
        return

    if key in ("reset", "overage-reset"):
        try:
            hours = float(value)
        except ValueError:
            pass
        else:
            if not math.isnan(hours):
                value = str(int(time.time()) + int(hours * 3600))

    if key == "claim" and value in _VALID_CLAIMS:
        if value == "five_hour":
            resets_at = int(time.time()) + 5 * 3600
        elif value in ("seven_day", "seven_day_opus", "seven_day_sonnet"):
            resets_at = int(time.time()) + 7 * 24 * 3600
        else:
            resets_at = int(time.time()) + 3600
        _exceeded_limits = [x for x in _exceeded_limits if x.type != value]
        _exceeded_limits.append(_ExceededLimit(type=value, resets_at=resets_at))  # type: ignore[arg-type]
        _update_representative_claim()
        return

    _mock_headers[full_key] = value
    if key in ("status", "overage-status"):
        _update_retry_after()

    if not _mock_headers:
        _mock_enabled = False


def add_exceeded_limit(limit_type: ExceededLimitType, hours_from_now: float) -> None:
    if not _is_ant():
        return
    global _mock_enabled, _mock_headers, _exceeded_limits
    _mock_enabled = True
    resets_at = int(time.time()) + int(hours_from_now * 3600)
    _exceeded_limits = [x for x in _exceeded_limits if x.type != limit_type]
    _exceeded_limits.append(_ExceededLimit(type=limit_type, resets_at=resets_at))
    if _exceeded_limits:
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
    _update_representative_claim()


def set_mock_early_warning(
    claim_abbrev: Literal["5h", "7d", "overage"],
    utilization: float,
    hours_from_now: float | None = None,
) -> None:
    if not _is_ant():
        return
    global _mock_enabled, _mock_headers
    _mock_enabled = True
    clear_mock_early_warning()
    default_hours = 4.0 if claim_abbrev == "5h" else 5.0 * 24
    hours = hours_from_now if hours_from_now is not None else default_hours
    resets_at = int(time.time()) + int(hours * 3600)
    prefix = f"anthropic-ratelimit-unified-{claim_abbrev}"
    _mock_headers[f"{prefix}-utilization"] = str(utilization)
    _mock_headers[f"{prefix}-reset"] = str(resets_at)
    _mock_headers[f"{prefix}-surpassed-threshold"] = str(utilization)
    if not _mock_headers.get("anthropic-ratelimit-unified-status"):
        _mock_headers["anthropic-ratelimit-unified-status"] = "allowed"


def clear_mock_early_warning() -> None:
    for k in (
        "anthropic-ratelimit-unified-5h-utilization",
        "anthropic-ratelimit-unified-5h-reset",
        "anthropic-ratelimit-unified-5h-surpassed-threshold",
        "anthropic-ratelimit-unified-7d-utilization",
        "anthropic-ratelimit-unified-7d-reset",
        "anthropic-ratelimit-unified-7d-surpassed-threshold",
    ):
        _mock_headers.pop(k, None)


def set_mock_rate_limit_scenario(scenario: MockScenario) -> None:
    global _mock_headers, _mock_enabled, _mock_headerless_429_message
    global _exceeded_limits, _mock_fast_mode_duration_ms, _mock_fast_mode_expires_at
    if not _is_ant():
        return

    if scenario == "clear":
        clear_mock_headers()
        return

    _mock_enabled = True
    five_hours = int(time.time()) + 5 * 3600
    seven_days = int(time.time()) + 7 * 24 * 3600

    _mock_headers = {}
    _mock_headerless_429_message = None

    if scenario not in ("fast-mode-limit", "fast-mode-short-limit"):
        _mock_fast_mode_duration_ms = None
        _mock_fast_mode_expires_at = None

    preserve = scenario in ("overage-active", "overage-warning", "overage-exhausted")
    if not preserve:
        _exceeded_limits.clear()

    if scenario == "normal":
        _mock_headers = {
            "anthropic-ratelimit-unified-status": "allowed",
            "anthropic-ratelimit-unified-reset": str(five_hours),
        }
    elif scenario == "session-limit-reached":
        _exceeded_limits = [_ExceededLimit(type="five_hour", resets_at=five_hours)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
    elif scenario == "approaching-weekly-limit":
        _mock_headers = {
            "anthropic-ratelimit-unified-status": "allowed_warning",
            "anthropic-ratelimit-unified-reset": str(seven_days),
            "anthropic-ratelimit-unified-representative-claim": "seven_day",
        }
    elif scenario == "weekly-limit-reached":
        _exceeded_limits = [_ExceededLimit(type="seven_day", resets_at=seven_days)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
    elif scenario == "overage-active":
        if not _exceeded_limits:
            _exceeded_limits = [_ExceededLimit(type="five_hour", resets_at=five_hours)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-status"] = "allowed"
        _mock_headers["anthropic-ratelimit-unified-overage-reset"] = str(_end_of_next_month_start_unix())
    elif scenario == "overage-warning":
        if not _exceeded_limits:
            _exceeded_limits = [_ExceededLimit(type="five_hour", resets_at=five_hours)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-status"] = "allowed_warning"
        _mock_headers["anthropic-ratelimit-unified-overage-reset"] = str(_end_of_next_month_start_unix())
    elif scenario == "overage-exhausted":
        if not _exceeded_limits:
            _exceeded_limits = [_ExceededLimit(type="five_hour", resets_at=five_hours)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-reset"] = str(_end_of_next_month_start_unix())
    elif scenario == "out-of-credits":
        if not _exceeded_limits:
            _exceeded_limits = [_ExceededLimit(type="five_hour", resets_at=five_hours)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-disabled-reason"] = "out_of_credits"
        _mock_headers["anthropic-ratelimit-unified-overage-reset"] = str(_end_of_next_month_start_unix())
    elif scenario == "org-zero-credit-limit":
        if not _exceeded_limits:
            _exceeded_limits = [_ExceededLimit(type="five_hour", resets_at=five_hours)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-disabled-reason"] = "org_service_zero_credit_limit"
        _mock_headers["anthropic-ratelimit-unified-overage-reset"] = str(_end_of_next_month_start_unix())
    elif scenario == "org-spend-cap-hit":
        if not _exceeded_limits:
            _exceeded_limits = [_ExceededLimit(type="five_hour", resets_at=five_hours)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-disabled-reason"] = "org_level_disabled_until"
        _mock_headers["anthropic-ratelimit-unified-overage-reset"] = str(_end_of_next_month_start_unix())
    elif scenario == "member-zero-credit-limit":
        if not _exceeded_limits:
            _exceeded_limits = [_ExceededLimit(type="five_hour", resets_at=five_hours)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-disabled-reason"] = "member_zero_credit_limit"
        _mock_headers["anthropic-ratelimit-unified-overage-reset"] = str(_end_of_next_month_start_unix())
    elif scenario == "seat-tier-zero-credit-limit":
        if not _exceeded_limits:
            _exceeded_limits = [_ExceededLimit(type="five_hour", resets_at=five_hours)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-status"] = "rejected"
        _mock_headers["anthropic-ratelimit-unified-overage-disabled-reason"] = "seat_tier_zero_credit_limit"
        _mock_headers["anthropic-ratelimit-unified-overage-reset"] = str(_end_of_next_month_start_unix())
    elif scenario == "opus-limit":
        _exceeded_limits = [_ExceededLimit(type="seven_day_opus", resets_at=seven_days)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
    elif scenario == "opus-warning":
        _mock_headers = {
            "anthropic-ratelimit-unified-status": "allowed_warning",
            "anthropic-ratelimit-unified-reset": str(seven_days),
            "anthropic-ratelimit-unified-representative-claim": "seven_day_opus",
        }
    elif scenario == "sonnet-limit":
        _exceeded_limits = [_ExceededLimit(type="seven_day_sonnet", resets_at=seven_days)]
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
    elif scenario == "sonnet-warning":
        _mock_headers = {
            "anthropic-ratelimit-unified-status": "allowed_warning",
            "anthropic-ratelimit-unified-reset": str(seven_days),
            "anthropic-ratelimit-unified-representative-claim": "seven_day_sonnet",
        }
    elif scenario == "fast-mode-limit":
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_fast_mode_duration_ms = 10 * 60 * 1000
        _mock_fast_mode_expires_at = None
    elif scenario == "fast-mode-short-limit":
        _update_representative_claim()
        _mock_headers["anthropic-ratelimit-unified-status"] = "rejected"
        _mock_fast_mode_duration_ms = 10 * 1000
        _mock_fast_mode_expires_at = None
    elif scenario == "extra-usage-required":
        _mock_headerless_429_message = "Extra usage is required for long context requests."


def get_mock_headerless_429_message() -> str | None:
    if not _is_ant():
        return None
    env_msg = os.environ.get("CLAUDE_MOCK_HEADERLESS_429")
    if env_msg:
        return env_msg
    if not _mock_enabled:
        return None
    return _mock_headerless_429_message


def get_mock_headers() -> MockHeaders | None:
    if not _mock_enabled or not _is_ant() or not _mock_headers:
        return None
    return dict(_mock_headers)


def get_mock_status() -> str:
    if not _mock_enabled or (not _mock_headers and not _mock_subscription_type):
        return "No mock headers active (using real limits)"
    lines = ["Active mock headers:"]
    effective = _mock_subscription_type or DEFAULT_MOCK_SUBSCRIPTION
    if _mock_subscription_type:
        lines.append(f"  Subscription Type: {_mock_subscription_type} (explicitly set)")
    else:
        lines.append(f"  Subscription Type: {effective} (default)")
    for key, value in sorted(_mock_headers.items()):
        lines.append(f"  {key}: {value}")
    if _exceeded_limits:
        lines.append("\nExceeded limits (contributing to representative claim):")
        for lim in _exceeded_limits:
            lines.append(f"  {lim.type}: resets at {lim.resets_at}")
    return "\n".join(lines)


def clear_mock_headers() -> None:
    global _mock_headers, _mock_enabled, _mock_headerless_429_message
    global _mock_subscription_type, _mock_fast_mode_duration_ms, _mock_fast_mode_expires_at
    global _exceeded_limits
    _mock_headers = {}
    _exceeded_limits.clear()
    _mock_subscription_type = None
    _mock_fast_mode_duration_ms = None
    _mock_fast_mode_expires_at = None
    _mock_headerless_429_message = None
    set_mock_billing_access_override(None)
    _mock_enabled = False


def apply_mock_headers(headers: dict[str, str]) -> dict[str, str]:
    mock = get_mock_headers()
    if not mock:
        return dict(headers)
    merged = dict(headers)
    merged.update(mock)
    return merged


def should_process_mock_limits() -> bool:
    if not _is_ant():
        return False
    return _mock_enabled or bool(os.environ.get("CLAUDE_MOCK_HEADERLESS_429"))


def get_current_mock_scenario() -> MockScenario | None:
    if not _mock_enabled:
        return None
    status = _mock_headers.get("anthropic-ratelimit-unified-status")
    overage = _mock_headers.get("anthropic-ratelimit-unified-overage-status")
    claim = _mock_headers.get("anthropic-ratelimit-unified-representative-claim")
    if claim == "seven_day_opus":
        return "opus-limit" if status == "rejected" else "opus-warning"
    if claim == "seven_day_sonnet":
        return "sonnet-limit" if status == "rejected" else "sonnet-warning"
    if overage == "rejected":
        return "overage-exhausted"
    if overage == "allowed_warning":
        return "overage-warning"
    if overage == "allowed":
        return "overage-active"
    if status == "rejected":
        if claim == "five_hour":
            return "session-limit-reached"
        if claim == "seven_day":
            return "weekly-limit-reached"
    if status == "allowed_warning" and claim == "seven_day":
        return "approaching-weekly-limit"
    if status == "allowed":
        return "normal"
    return None


def get_scenario_description(scenario: MockScenario) -> str:
    descriptions: dict[str, str] = {
        "normal": "Normal usage, no limits",
        "session-limit-reached": "Session rate limit exceeded",
        "approaching-weekly-limit": "Approaching weekly aggregate limit",
        "weekly-limit-reached": "Weekly aggregate limit exceeded",
        "overage-active": "Using extra usage (overage active)",
        "overage-warning": "Approaching extra usage limit",
        "overage-exhausted": "Both subscription and extra usage limits exhausted",
        "out-of-credits": "Out of extra usage credits (wallet empty)",
        "org-zero-credit-limit": "Org spend cap is zero (no extra usage budget)",
        "org-spend-cap-hit": "Org spend cap hit for the month",
        "member-zero-credit-limit": "Member limit is zero (admin can allocate more)",
        "seat-tier-zero-credit-limit": "Seat tier limit is zero (admin can allocate more)",
        "opus-limit": "Opus limit reached",
        "opus-warning": "Approaching Opus limit",
        "sonnet-limit": "Sonnet limit reached",
        "sonnet-warning": "Approaching Sonnet limit",
        "fast-mode-limit": "Fast mode rate limit",
        "fast-mode-short-limit": "Fast mode rate limit (short)",
        "extra-usage-required": "Headerless 429: Extra usage required for 1M context",
        "clear": "Clear mock headers (use real limits)",
    }
    return descriptions.get(scenario, "Unknown scenario")


def set_mock_subscription_type(subscription_type: SubscriptionType) -> None:
    global _mock_enabled, _mock_subscription_type
    if not _is_ant():
        return
    _mock_enabled = True
    _mock_subscription_type = subscription_type


def get_mock_subscription_type() -> SubscriptionType | None:
    if not _mock_enabled or not _is_ant():
        return None
    return _mock_subscription_type or DEFAULT_MOCK_SUBSCRIPTION


def should_use_mock_subscription() -> bool:
    return bool(_mock_enabled and _mock_subscription_type is not None and _is_ant())


def set_mock_billing_access(has_access: bool | None) -> None:
    global _mock_enabled
    if not _is_ant():
        return
    _mock_enabled = True
    set_mock_billing_access_override(has_access)


def is_mock_fast_mode_rate_limit_scenario() -> bool:
    return _mock_fast_mode_duration_ms is not None


def check_mock_fast_mode_rate_limit(
    is_fast_mode_active: bool | None = None,
) -> MockHeaders | None:
    global _mock_fast_mode_expires_at
    if _mock_fast_mode_duration_ms is None:
        return None
    if not is_fast_mode_active:
        return None
    now_ms = time.time() * 1000
    if _mock_fast_mode_expires_at is not None and now_ms >= _mock_fast_mode_expires_at:
        clear_mock_headers()
        return None
    if _mock_fast_mode_expires_at is None:
        _mock_fast_mode_expires_at = now_ms + _mock_fast_mode_duration_ms
    remaining_ms = _mock_fast_mode_expires_at - now_ms
    headers = dict(_mock_headers)
    headers["retry-after"] = str(max(1, int((remaining_ms + 999) // 1000)))
    return headers


def reset_mock_rate_limits_state_for_tests() -> None:
    """Clear all module state (tests only)."""
    clear_mock_headers()
