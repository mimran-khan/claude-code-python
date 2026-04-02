"""Auto-mode session flags (``utils/permissions/autoModeState.ts``) — minimal port."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AutoModeState:
    enabled: bool = False
    blocked_reason: str | None = None
    notes: dict[str, str] = field(default_factory=dict)


_state = AutoModeState()


def get_auto_mode_state() -> AutoModeState:
    return _state


def set_auto_mode_state(**kwargs: object) -> None:
    global _state
    cur = vars(_state).copy()
    for k, v in kwargs.items():
        if k in cur:
            cur[k] = v
    _state = AutoModeState(**cur)
