"""
Migrated from: commands/permissions/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class PermissionsCommand(Command):
    @property
    def name(self) -> str:
        return "permissions"

    @property
    def aliases(self) -> list[str]:
        return ["allowed-tools"]

    @property
    def description(self) -> str:
        return "Manage allow & deny tool permission rules"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "permissions"},
        )
