"""
Migrated from: commands/keybindings/index.ts

Handler: :mod:`claude_code.commands.keybindings.keybindings` (``commands/keybindings/keybindings.ts``).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult


@dataclass(frozen=True)
class KeybindingsMetadata:
    name: str = "keybindings"
    description: str = "Open or create your keybindings configuration file"
    command_type: str = "local"
    supports_non_interactive: bool = False


keybindings_metadata = KeybindingsMetadata()


class KeybindingsCommand(Command):
    @property
    def name(self) -> str:
        return keybindings_metadata.name

    @property
    def description(self) -> str:
        return keybindings_metadata.description

    async def execute(self, context: CommandContext) -> CommandResult:
        from .keybindings import call

        r = await call()
        return CommandResult(success=True, message=r.value)
