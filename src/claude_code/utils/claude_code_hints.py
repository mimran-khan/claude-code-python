"""
Pending Claude Code hint slot (stderr protocol).

Migrated from: utils/claudeCodeHints.ts (store subset).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ClaudeCodeHintType = Literal["plugin"]


@dataclass
class ClaudeCodeHint:
    v: int
    type: ClaudeCodeHintType
    value: str
    source_command: str


_pending: ClaudeCodeHint | None = None
_shown_this_session = False


def set_pending_hint(hint: ClaudeCodeHint) -> None:
    global _pending
    if _shown_this_session:
        return
    _pending = hint


def clear_pending_hint() -> None:
    global _pending
    _pending = None


def mark_shown_this_session() -> None:
    global _shown_this_session
    _shown_this_session = True


def get_pending_hint_snapshot() -> ClaudeCodeHint | None:
    return _pending


def has_shown_hint_this_session() -> bool:
    return _shown_this_session


def reset_claude_code_hint_store_for_testing() -> None:
    global _pending, _shown_this_session
    _pending = None
    _shown_this_session = False


__all__ = [
    "ClaudeCodeHint",
    "clear_pending_hint",
    "get_pending_hint_snapshot",
    "has_shown_hint_this_session",
    "mark_shown_this_session",
    "reset_claude_code_hint_store_for_testing",
    "set_pending_hint",
]
