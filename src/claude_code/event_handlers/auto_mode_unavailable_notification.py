"""
Detect permission-mode carousel wrap past unavailable auto mode.

Migrated from: hooks/notifs/useAutoModeUnavailableNotification.ts
"""

from __future__ import annotations


def wrapped_past_auto_slot(
    *,
    mode: str,
    prev_mode: str,
    is_auto_mode_available: bool,
    has_auto_mode_opt_in: bool,
) -> bool:
    return bool(
        mode == "default"
        and prev_mode != "default"
        and prev_mode != "auto"
        and not is_auto_mode_available
        and has_auto_mode_opt_in
    )
