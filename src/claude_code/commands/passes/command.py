"""
Migrated from: commands/passes/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class PassesCommand(Command):
    def __init__(self, *, reward_cached: bool = False) -> None:
        self._reward_cached = reward_cached

    @property
    def name(self) -> str:
        return "passes"

    @property
    def description(self) -> str:
        if self._reward_cached:
            return "Share a free week of Claude Code with friends and earn extra usage"
        return "Share a free week of Claude Code with friends"

    @property
    def hidden(self) -> bool:
        return False

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "passes"},
        )
