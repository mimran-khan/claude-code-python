"""
Migrated from: commands/mcp/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class McpCommand(Command):
    @property
    def name(self) -> str:
        return "mcp"

    @property
    def description(self) -> str:
        return "Manage MCP servers"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={
                "action": "load_jsx",
                "module": "mcp",
                "immediate": True,
                "argument_hint": "[enable|disable [server-name]]",
                "args": context.args,
            },
        )
