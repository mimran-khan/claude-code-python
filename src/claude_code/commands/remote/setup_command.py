"""
Migrated from: commands/remote-setup/index.ts (command name: web-setup).
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


def web_setup_is_enabled(
    *,
    feature_cobalt_lantern: bool = False,
    allow_remote_sessions: bool = True,
) -> bool:
    return feature_cobalt_lantern and allow_remote_sessions


def web_setup_is_hidden(*, allow_remote_sessions: bool = True) -> bool:
    return not allow_remote_sessions


class WebSetupCommand(Command):
    def __init__(
        self,
        *,
        feature_cobalt_lantern: bool = False,
        allow_remote_sessions: bool = True,
    ) -> None:
        self._cobalt = feature_cobalt_lantern
        self._allow_remote = allow_remote_sessions

    @property
    def name(self) -> str:
        return "web-setup"

    @property
    def description(self) -> str:
        return "Setup Claude Code on the web (requires connecting your GitHub account)"

    @property
    def hidden(self) -> bool:
        return web_setup_is_hidden(allow_remote_sessions=self._allow_remote)

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        if not web_setup_is_enabled(
            feature_cobalt_lantern=self._cobalt,
            allow_remote_sessions=self._allow_remote,
        ):
            return CommandResult(success=False, message="Web setup not available.")
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "remote-setup"},
        )
