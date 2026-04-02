"""
Base command types and definitions.

Migrated from: commands.ts
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

CommandType = Literal["local", "local-jsx", "prompt"]


@dataclass
class CommandContext:
    """Context provided to command execution."""

    cwd: str
    args: list[str] = field(default_factory=list)
    flags: dict[str, Any] = field(default_factory=dict)
    get_app_state: Callable[[], Any] | None = None
    set_app_state: Callable[[Any], None] | None = None


@dataclass
class CommandResult:
    """Result of command execution."""

    success: bool
    message: str | None = None
    output: Any = None
    error: str | None = None


class Command(ABC):
    """Base class for all commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The command name (used with / prefix)."""
        pass

    @property
    def aliases(self) -> list[str]:
        """Alternative names for the command."""
        return []

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of what the command does."""
        pass

    @property
    def command_type(self) -> CommandType:
        """The type of command."""
        return "local"

    @property
    def hidden(self) -> bool:
        """Whether the command is hidden from help."""
        return False

    @property
    def requires_auth(self) -> bool:
        """Whether the command requires authentication."""
        return False

    @abstractmethod
    async def execute(self, context: CommandContext) -> CommandResult:
        """Execute the command."""
        pass

    def get_help(self) -> str:
        """Get detailed help text for the command."""
        return self.description


@dataclass
class CommandDef:
    """Command definition for registration."""

    name: str
    description: str
    execute: Callable[[CommandContext], Awaitable[CommandResult]]
    aliases: list[str] = field(default_factory=list)
    command_type: CommandType = "local"
    hidden: bool = False
    requires_auth: bool = False
    help_text: str | None = None


def build_command(cmd_def: CommandDef) -> Command:
    """Build a Command instance from a CommandDef."""

    class BuiltCommand(Command):
        @property
        def name(self) -> str:
            return cmd_def.name

        @property
        def aliases(self) -> list[str]:
            return cmd_def.aliases

        @property
        def description(self) -> str:
            return cmd_def.description

        @property
        def command_type(self) -> CommandType:
            return cmd_def.command_type

        @property
        def hidden(self) -> bool:
            return cmd_def.hidden

        @property
        def requires_auth(self) -> bool:
            return cmd_def.requires_auth

        async def execute(self, context: CommandContext) -> CommandResult:
            return await cmd_def.execute(context)

        def get_help(self) -> str:
            return cmd_def.help_text or cmd_def.description

    return BuiltCommand()
