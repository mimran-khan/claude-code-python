"""
Migrated from: commands/model/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ModelCommand(Command):
    def __init__(
        self,
        *,
        render_model_name: str = "(unknown)",
        immediate: bool = False,
    ) -> None:
        self._render_model_name = render_model_name
        self._immediate = immediate

    @property
    def name(self) -> str:
        return "model"

    @property
    def description(self) -> str:
        return f"Set the AI model for Claude Code (currently {self._render_model_name})"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={
                "action": "load_jsx",
                "module": "model",
                "immediate": self._immediate,
                "argument_hint": "[model]",
                "args": context.args,
            },
        )
