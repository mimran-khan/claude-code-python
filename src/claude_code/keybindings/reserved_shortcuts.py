"""
Reserved / non-rebindable shortcuts and key normalization.

Migrated from: keybindings/reservedShortcuts.ts
"""

from __future__ import annotations

from .platform import get_platform
from .types import ReservedShortcut

NON_REBINDABLE: list[ReservedShortcut] = [
    ReservedShortcut(
        key="ctrl+c",
        reason="Cannot be rebound - used for interrupt/exit (hardcoded)",
        severity="error",
    ),
    ReservedShortcut(
        key="ctrl+d",
        reason="Cannot be rebound - used for exit (hardcoded)",
        severity="error",
    ),
    ReservedShortcut(
        key="ctrl+m",
        reason="Cannot be rebound - identical to Enter in terminals (both send CR)",
        severity="error",
    ),
]

TERMINAL_RESERVED: list[ReservedShortcut] = [
    ReservedShortcut(
        key="ctrl+z",
        reason="Unix process suspend (SIGTSTP)",
        severity="warning",
    ),
    ReservedShortcut(
        key="ctrl+\\",
        reason="Terminal quit signal (SIGQUIT)",
        severity="error",
    ),
]

MACOS_RESERVED: list[ReservedShortcut] = [
    ReservedShortcut(key="cmd+c", reason="macOS system copy", severity="error"),
    ReservedShortcut(key="cmd+v", reason="macOS system paste", severity="error"),
    ReservedShortcut(key="cmd+x", reason="macOS system cut", severity="error"),
    ReservedShortcut(key="cmd+q", reason="macOS quit application", severity="error"),
    ReservedShortcut(key="cmd+w", reason="macOS close window/tab", severity="error"),
    ReservedShortcut(key="cmd+tab", reason="macOS app switcher", severity="error"),
    ReservedShortcut(key="cmd+space", reason="macOS Spotlight", severity="error"),
]


def get_reserved_shortcuts() -> list[ReservedShortcut]:
    """All reserved shortcuts for the current platform."""
    reserved = [*NON_REBINDABLE, *TERMINAL_RESERVED]
    if get_platform() == "macos":
        reserved.extend(MACOS_RESERVED)
    return reserved


def normalize_step(step: str) -> str:
    """Normalize one chord step: lowercase modifiers sorted, then main key."""
    parts = step.split("+")
    modifiers: list[str] = []
    main_key = ""

    modifier_aliases = {
        "ctrl",
        "control",
        "alt",
        "opt",
        "option",
        "meta",
        "cmd",
        "command",
        "shift",
    }

    for part in parts:
        lower = part.strip().lower()
        if lower in modifier_aliases or lower in ("super", "win"):
            if lower == "control":
                modifiers.append("ctrl")
            elif lower in ("option", "opt"):
                modifiers.append("alt")
            elif lower in ("command", "cmd", "super", "win"):
                modifiers.append("cmd")
            else:
                modifiers.append(lower)
        else:
            main_key = lower

    modifiers.sort()
    return "+".join([*modifiers, main_key])


def normalize_key_for_comparison(key: str) -> str:
    """
    Normalize a full key string for comparison (lowercase, sorted modifiers per step).

    Chords are space-separated; each step is normalized independently.
    """
    return " ".join(normalize_step(s) for s in key.strip().split())
