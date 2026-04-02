"""
Migrated from: commands/output-style/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class OutputStyleCommand(Command):
    @property
    def name(self) -> str:
        return "output-style"

    @property
    def description(self) -> str:
        return "Deprecated: use /config to change output style"

    @property
    def hidden(self) -> bool:
        return True

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "output-style"},
        )
