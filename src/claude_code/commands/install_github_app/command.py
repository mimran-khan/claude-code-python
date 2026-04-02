"""
Migrated from: commands/install-github-app/index.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult


def _is_env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class InstallGitHubAppMetadata:
    command_type: str = "local-jsx"
    name: str = "install-github-app"
    description: str = "Set up Claude GitHub Actions for a repository"
    availability: tuple[str, ...] = ("claude-ai", "console")


install_github_app_metadata = InstallGitHubAppMetadata()


def is_install_github_app_enabled() -> bool:
    return not _is_env_truthy(os.environ.get("DISABLE_INSTALL_GITHUB_APP_COMMAND"))


class InstallGitHubAppCommand(Command):
    @property
    def name(self) -> str:
        return install_github_app_metadata.name

    @property
    def description(self) -> str:
        return install_github_app_metadata.description

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        if not is_install_github_app_enabled():
            return CommandResult(success=False, message="Command disabled by policy.")
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "install-github-app"},
        )
