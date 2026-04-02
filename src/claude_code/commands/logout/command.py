"""
Migrated from: commands/logout/index.ts
"""

from __future__ import annotations

import os

from ..base import Command, CommandContext, CommandResult


def _is_env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in ("1", "true", "yes", "on")


def logout_is_enabled() -> bool:
    return not _is_env_truthy(os.environ.get("DISABLE_LOGOUT_COMMAND"))


class LogoutCommand(Command):
    @property
    def name(self) -> str:
        return "logout"

    @property
    def description(self) -> str:
        return "Sign out from your Anthropic account"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        if not logout_is_enabled():
            return CommandResult(success=False, message="Logout command disabled.")
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "logout"},
        )
