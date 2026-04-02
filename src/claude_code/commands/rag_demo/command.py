"""
RagDemo command placeholder.

RAG demo command placeholder.
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class RagDemoCommand(Command):
    @property
    def name(self) -> str:
        return "rag-demo"

    @property
    def description(self) -> str:
        return "RAG demo command placeholder."

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "rag-demo", "args": context.args},
        )
