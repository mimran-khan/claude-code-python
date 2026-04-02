"""Compact warning suppression flag (replaces React store from compactWarningState.ts)."""

from __future__ import annotations

_compact_warning_suppressed: bool = False


def suppress_compact_warning() -> None:
    global _compact_warning_suppressed
    _compact_warning_suppressed = True


def clear_compact_warning_suppression() -> None:
    global _compact_warning_suppressed
    _compact_warning_suppressed = False


def is_compact_warning_suppressed() -> bool:
    return _compact_warning_suppressed
