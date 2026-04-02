"""
Migrated from: commands/hooks/index.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult


@dataclass(frozen=True)
class HooksCommandMetadata:
    """Static command registration fields (mirrors TS `satisfies Command`)."""

    command_type: str = "local-jsx"
    name: str = "hooks"
    description: str = "View hook configurations for tool events"
    immediate: bool = True


hooks_command_metadata = HooksCommandMetadata()


class HooksCommand(Command):
    """View hook configurations for tool events."""

    @property
    def name(self) -> str:
        return hooks_command_metadata.name

    @property
    def description(self) -> str:
        return hooks_command_metadata.description

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Load hooks UI module (parity: hooks.tsx).",
            output={"action": "load_jsx", "module": "hooks"},
        )
