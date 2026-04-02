"""
/agents — manage agent configurations (lazy UI).

Migrated from: commands/agents/index.ts
"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

AGENTS_COMMAND = CommandSpec(
    type="local-jsx",
    name="agents",
    description="Manage agent configurations",
    load_symbol="claude_code.commands.agents.ui",
)

__all__ = ["AGENTS_COMMAND"]
