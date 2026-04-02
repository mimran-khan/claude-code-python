"""
Migrated from: commands/install-slack-app/index.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult


@dataclass(frozen=True)
class InstallSlackAppMetadata:
    command_type: str = "local"
    name: str = "install-slack-app"
    description: str = "Install the Claude Slack app"
    availability: tuple[str, ...] = ("claude-ai",)
    supports_non_interactive: bool = False


install_slack_app_metadata = InstallSlackAppMetadata()


class InstallSlackAppCommand(Command):
    @property
    def name(self) -> str:
        return install_slack_app_metadata.name

    @property
    def description(self) -> str:
        return install_slack_app_metadata.description

    async def execute(self, context: CommandContext) -> CommandResult:
        from .install_slack_app import call

        result = await call()
        return CommandResult(success=True, message=result.value, output=result.__dict__)
