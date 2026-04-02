"""
Command registry.

Register and look up commands.

Migrated from: commands.ts
"""

from __future__ import annotations

from .base import Command, CommandDef, build_command


class CommandRegistry:
    """Registry for all available commands."""

    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._aliases: dict[str, str] = {}

    def register(self, command: Command) -> None:
        """Register a command."""
        self._commands[command.name] = command

        for alias in command.aliases:
            self._aliases[alias] = command.name

    def register_def(self, cmd_def: CommandDef) -> None:
        """Register a command from a definition."""
        command = build_command(cmd_def)
        self.register(command)

    def get(self, name: str) -> Command | None:
        """Get a command by name or alias."""
        # Check direct name
        if name in self._commands:
            return self._commands[name]

        # Check aliases
        if name in self._aliases:
            actual_name = self._aliases[name]
            return self._commands.get(actual_name)

        return None

    def get_all(self) -> list[Command]:
        """Get all registered commands."""
        return list(self._commands.values())

    def get_visible(self) -> list[Command]:
        """Get all non-hidden commands."""
        return [cmd for cmd in self._commands.values() if not cmd.hidden]

    def has(self, name: str) -> bool:
        """Check if a command exists."""
        return name in self._commands or name in self._aliases


# Global registry instance
_registry = CommandRegistry()


def register_command(command: Command) -> None:
    """Register a command in the global registry."""
    _registry.register(command)


def get_command(name: str) -> Command | None:
    """Get a command from the global registry."""
    return _registry.get(name)


def get_all_commands() -> list[Command]:
    """Get all commands from the global registry."""
    return _registry.get_all()


def get_visible_commands() -> list[Command]:
    """Get all visible commands from the global registry."""
    return _registry.get_visible()
