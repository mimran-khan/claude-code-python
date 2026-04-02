"""
Migrated from: commands/ide/index.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult


@dataclass(frozen=True)
class IdeCommandMetadata:
    command_type: str = "local-jsx"
    name: str = "ide"
    description: str = "Manage IDE integrations and show status"
    argument_hint: str = "[open]"


ide_command_metadata = IdeCommandMetadata()


class IdeCommand(Command):
    @property
    def name(self) -> str:
        return ide_command_metadata.name

    @property
    def description(self) -> str:
        return ide_command_metadata.description

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "ide", "args": context.args},
        )
