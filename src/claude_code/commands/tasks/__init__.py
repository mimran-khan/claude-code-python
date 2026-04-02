"""Migrated from: commands/tasks/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

TASKS_COMMAND = CommandSpec(
    type="local-jsx",
    name="tasks",
    description="List and manage background tasks",
    aliases=("bashes",),
    load_symbol="claude_code.commands.tasks.ui",
)

__all__ = ["TASKS_COMMAND"]
