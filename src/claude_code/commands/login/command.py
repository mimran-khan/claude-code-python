"""
Migrated from: commands/login/index.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult


def _is_env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in ("1", "true", "yes", "on")


def login_is_enabled() -> bool:
    return not _is_env_truthy(os.environ.get("DISABLE_LOGIN_COMMAND"))


def login_description(has_anthropic_api_key_auth: bool = False) -> str:
    if has_anthropic_api_key_auth:
        return "Switch Anthropic accounts"
    return "Sign in with your Anthropic account"


@dataclass(frozen=True)
class LoginMetadata:
    command_type: str = "local-jsx"
    name: str = "login"


class LoginCommand(Command):
    def __init__(self, has_anthropic_api_key_auth: bool = False) -> None:
        self._has_api_key = has_anthropic_api_key_auth

    @property
    def name(self) -> str:
        return LoginMetadata().name

    @property
    def description(self) -> str:
        return login_description(self._has_api_key)

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        if not login_is_enabled():
            return CommandResult(success=False, message="Login command disabled.")
        return CommandResult(
            success=True,
            message="Starting authentication…",
            output={"action": "load_jsx", "module": "login"},
        )
