"""
Recent auto-mode classifier denials (for permissions UI).

Migrated from: utils/autoModeDenials.ts

The TypeScript build gates recording on ``feature('TRANSCRIPT_CLASSIFIER')``;
Python always records unless tests clear the store (no Bun bundle feature flag).
"""

from __future__ import annotations

from dataclasses import dataclass

_MAX_DENIALS = 20
_denials: list[AutoModeDenial] = []


@dataclass(frozen=True)
class AutoModeDenial:
    tool_name: str
    display: str
    reason: str
    timestamp: float


def record_auto_mode_denial(denial: AutoModeDenial) -> None:
    global _denials
    _denials = [denial, *_denials[: _MAX_DENIALS - 1]]


def get_auto_mode_denials() -> tuple[AutoModeDenial, ...]:
    return tuple(_denials)


def clear_auto_mode_denials_for_tests() -> None:
    """Reset store (tests only)."""
    global _denials
    _denials = []
