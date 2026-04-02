"""
Plugin command.

Manage plugins.

Migrated from: commands/plugin/*.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class PluginCommand(Command):
    """Manage plugins."""

    @property
    def name(self) -> str:
        return "plugin"

    @property
    def aliases(self) -> list[str]:
        return ["plugins"]

    @property
    def description(self) -> str:
        return "Manage plugins"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Manage plugins."""
        args = context.args

        if not args:
            return CommandResult(
                success=True,
                message="Plugin Commands: list, install, uninstall, enable, disable, update",
                output={"action": "showPluginHelp"},
            )

        subcommand = args[0]

        if subcommand == "list":
            return CommandResult(
                success=True,
                output={"plugins": [], "message": "No plugins installed."},
            )

        elif subcommand == "install":
            if len(args) < 2:
                return CommandResult(
                    success=False,
                    error="Usage: /plugin install <plugin-name>",
                )
            plugin_name = args[1]
            return CommandResult(
                success=True,
                message=f"Installing plugin: {plugin_name}",
            )

        elif subcommand == "uninstall":
            if len(args) < 2:
                return CommandResult(
                    success=False,
                    error="Usage: /plugin uninstall <plugin-name>",
                )
            plugin_name = args[1]
            return CommandResult(
                success=True,
                message=f"Uninstalling plugin: {plugin_name}",
            )

        elif subcommand == "enable":
            if len(args) < 2:
                return CommandResult(
                    success=False,
                    error="Usage: /plugin enable <plugin-name>",
                )
            plugin_name = args[1]
            return CommandResult(
                success=True,
                message=f"Enabling plugin: {plugin_name}",
            )

        elif subcommand == "disable":
            if len(args) < 2:
                return CommandResult(
                    success=False,
                    error="Usage: /plugin disable <plugin-name>",
                )
            plugin_name = args[1]
            return CommandResult(
                success=True,
                message=f"Disabling plugin: {plugin_name}",
            )

        elif subcommand == "update":
            plugin_name = args[1] if len(args) > 1 else None
            if plugin_name:
                return CommandResult(
                    success=True,
                    message=f"Updating plugin: {plugin_name}",
                )
            return CommandResult(
                success=True,
                message="Updating all plugins...",
            )

        return CommandResult(
            success=False,
            error=f"Unknown subcommand: {subcommand}",
        )
