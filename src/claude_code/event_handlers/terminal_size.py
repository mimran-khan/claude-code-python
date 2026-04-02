"""
Terminal columns/rows for layout (Ink context equivalent).

Migrated from: hooks/useTerminalSize.ts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TerminalSize:
    columns: int
    rows: int


def require_terminal_size(ctx: TerminalSize | None) -> TerminalSize:
    if ctx is None:
        msg = "terminal size context is required (use TerminalSize(columns=..., rows=...))"
        raise RuntimeError(msg)
    return ctx
