"""
Migrated from: commands/status/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class StatusCommand(Command):
    @property
    def name(self) -> str:
        return "status"

    @property
    def description(self) -> str:
        return "Show Claude Code status including version, model, account, API connectivity, and tool statuses"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "status", "immediate": True},
        )
