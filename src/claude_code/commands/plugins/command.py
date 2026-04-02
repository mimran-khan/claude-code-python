"""
Migrated from: commands/plugin/index.tsx
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class PluginCommand(Command):
    @property
    def name(self) -> str:
        return "plugin"

    @property
    def aliases(self) -> list[str]:
        return ["plugins", "marketplace"]

    @property
    def description(self) -> str:
        return "Manage Claude Code plugins"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={
                "action": "load_jsx",
                "module": "plugin",
                "immediate": True,
                "args": context.args,
            },
        )
