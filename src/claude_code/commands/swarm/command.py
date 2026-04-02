"""
Swarm command placeholder.

Agent swarm placeholder.
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class SwarmCommand(Command):
    @property
    def name(self) -> str:
        return "swarm"

    @property
    def description(self) -> str:
        return "Agent swarm placeholder."

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "swarm", "args": context.args},
        )
