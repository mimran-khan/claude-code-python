"""
Migrated from: commands/memory/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class MemoryCommand(Command):
    @property
    def name(self) -> str:
        return "memory"

    @property
    def description(self) -> str:
        return "Edit Claude memory files"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "memory"},
        )
