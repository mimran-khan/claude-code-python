"""
Migrated from: commands/remote-env/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


def remote_env_is_enabled(
    *,
    is_claude_ai_subscriber: bool = False,
    allow_remote_sessions: bool = True,
) -> bool:
    return is_claude_ai_subscriber and allow_remote_sessions


def remote_env_is_hidden(
    *,
    is_claude_ai_subscriber: bool = False,
    allow_remote_sessions: bool = True,
) -> bool:
    return not is_claude_ai_subscriber or not allow_remote_sessions


class RemoteEnvCommand(Command):
    def __init__(
        self,
        *,
        is_claude_ai_subscriber: bool = False,
        allow_remote_sessions: bool = True,
    ) -> None:
        self._subscriber = is_claude_ai_subscriber
        self._allow_remote = allow_remote_sessions

    @property
    def name(self) -> str:
        return "remote-env"

    @property
    def description(self) -> str:
        return "Configure the default remote environment for teleport sessions"

    @property
    def hidden(self) -> bool:
        return remote_env_is_hidden(
            is_claude_ai_subscriber=self._subscriber,
            allow_remote_sessions=self._allow_remote,
        )

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        if not remote_env_is_enabled(
            is_claude_ai_subscriber=self._subscriber,
            allow_remote_sessions=self._allow_remote,
        ):
            return CommandResult(success=False, message="Remote env not available.")
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "remote-env"},
        )
