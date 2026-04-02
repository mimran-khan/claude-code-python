"""
One-shot notification when focus returns and clipboard holds an image.

Migrated from: hooks/useClipboardImageHint.ts
"""

from __future__ import annotations

from dataclasses import dataclass

NOTIFICATION_KEY = "clipboard-image-hint"
FOCUS_CHECK_DEBOUNCE_MS = 1000
FOCUS_CHECK_DEBOUNCE_S = FOCUS_CHECK_DEBOUNCE_MS / 1000.0
HINT_COOLDOWN_MS = 30000


@dataclass
class ClipboardImageHintState:
    last_focused: bool = False
    last_hint_time_ms: float = 0.0


def should_run_focus_regain_check(
    state: ClipboardImageHintState,
    *,
    is_focused: bool,
    enabled: bool,
    now_ms: float,
) -> bool:
    """Return True when we transitioned to focused and should debounce-check clipboard."""
    was_focused = state.last_focused
    state.last_focused = is_focused
    return enabled and is_focused and not was_focused


def hint_cooldown_blocks(now_ms: float, state: ClipboardImageHintState) -> bool:
    return now_ms - state.last_hint_time_ms < HINT_COOLDOWN_MS


def mark_hint_shown(state: ClipboardImageHintState, now_ms: float) -> None:
    state.last_hint_time_ms = now_ms
