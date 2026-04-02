"""Migrated from: commands/diff/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

DIFF_COMMAND = CommandSpec(
    type="local-jsx",
    name="diff",
    description="View uncommitted changes and per-turn diffs",
    load_symbol="claude_code.commands.diff.ui",
)

__all__ = ["DIFF_COMMAND"]
