"""
Shared blink phase from a monotonic animation clock (Ink useAnimationFrame port).

Migrated from: hooks/useBlink.ts
"""

from __future__ import annotations

BLINK_INTERVAL_MS = 600


def blink_visible(
    time_ms: float,
    *,
    interval_ms: float = BLINK_INTERVAL_MS,
) -> bool:
    """Even interval → visible; odd → hidden (TS: floor(time/interval) % 2 == 0)."""
    if interval_ms <= 0:
        return True
    return int(time_ms // interval_ms) % 2 == 0


def blink_should_run(*, enabled: bool, terminal_focused: bool) -> bool:
    return bool(enabled and terminal_focused)
