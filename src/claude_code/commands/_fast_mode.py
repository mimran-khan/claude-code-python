"""Fast mode helpers — re-exports ``utils.fast_mode`` (ported from utils/fastMode.ts)."""

from __future__ import annotations

from claude_code.utils.fast_mode import (
    FAST_MODE_MODEL_DISPLAY,
    clear_fast_mode_cooldown,
    get_fast_mode_model,
    get_fast_mode_runtime_state,
    get_fast_mode_unavailable_reason,
    is_fast_mode_available,
    is_fast_mode_cooldown,
    is_fast_mode_enabled,
    on_cooldown_expired,
    on_cooldown_triggered,
    on_org_fast_mode_changed,
    prefetch_fast_mode_status,
    trigger_fast_mode_cooldown,
)

__all__ = [
    "FAST_MODE_MODEL_DISPLAY",
    "clear_fast_mode_cooldown",
    "get_fast_mode_model",
    "get_fast_mode_runtime_state",
    "get_fast_mode_unavailable_reason",
    "is_fast_mode_available",
    "is_fast_mode_cooldown",
    "is_fast_mode_enabled",
    "on_cooldown_expired",
    "on_cooldown_triggered",
    "on_org_fast_mode_changed",
    "prefetch_fast_mode_status",
    "trigger_fast_mode_cooldown",
]
