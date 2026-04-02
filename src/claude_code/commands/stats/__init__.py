"""Migrated from: commands/stats/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

STATS_COMMAND = CommandSpec(
    type="local-jsx",
    name="stats",
    description="Show your Claude Code usage statistics and activity",
    load_symbol="claude_code.commands.stats.ui",
)

__all__ = ["STATS_COMMAND"]
