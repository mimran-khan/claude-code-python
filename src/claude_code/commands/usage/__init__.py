"""Migrated from: commands/usage/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

USAGE_COMMAND = CommandSpec(
    type="local-jsx",
    name="usage",
    description="Show plan usage limits",
    availability=("claude-ai",),
    load_symbol="claude_code.commands.usage.ui",
)

__all__ = ["USAGE_COMMAND"]
