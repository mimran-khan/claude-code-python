"""
Migrated from: commands/upgrade/index.ts
"""

from __future__ import annotations

import os

from ..base import Command, CommandContext, CommandResult


def _is_env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in ("1", "true", "yes", "on")


def upgrade_is_enabled(subscription_type: str | None = None) -> bool:
    if _is_env_truthy(os.environ.get("DISABLE_UPGRADE_COMMAND")):
        return False
    st = subscription_type or os.environ.get("SUBSCRIPTION_TYPE", "")
    return st != "enterprise"


class UpgradeCommand(Command):
    @property
    def name(self) -> str:
        return "upgrade"

    @property
    def description(self) -> str:
        return "Upgrade to Max for higher rate limits and more Opus"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        if not upgrade_is_enabled():
            return CommandResult(success=False, message="Upgrade command disabled.")
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "upgrade"},
        )
