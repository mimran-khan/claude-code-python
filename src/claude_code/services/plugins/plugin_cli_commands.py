"""
CLI-oriented plugin commands (no sys.exit; return outcomes for Typer/main).

Migrated from: services/plugins/pluginCliCommands.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from ...utils.log import log_error
from . import operations
from .operations import InstallableScope, PluginScope


@dataclass
class CliCommandResult:
    ok: bool
    message: str


async def install_plugin_cli(plugin: str, scope: InstallableScope = "user") -> CliCommandResult:
    try:
        result = await operations.install_plugin(plugin, scope)
        if not result.success:
            return CliCommandResult(False, result.message)
        return CliCommandResult(True, result.message)
    except Exception as err:
        log_error(err if isinstance(err, Exception) else RuntimeError(str(err)))
        return CliCommandResult(False, str(err))


async def uninstall_plugin_cli(
    plugin: str,
    scope: InstallableScope | None = "user",
) -> CliCommandResult:
    try:
        result = await operations.uninstall_plugin(plugin, scope)
        if not result.success:
            return CliCommandResult(False, result.message)
        return CliCommandResult(True, result.message)
    except Exception as err:
        log_error(err if isinstance(err, Exception) else RuntimeError(str(err)))
        return CliCommandResult(False, str(err))


async def enable_plugin_cli(
    plugin: str,
    scope: InstallableScope | None = None,
) -> CliCommandResult:
    try:
        eff: InstallableScope = scope if scope is not None else "user"
        result = await operations.enable_plugin(plugin, eff)
        if not result.success:
            return CliCommandResult(False, result.message)
        return CliCommandResult(True, result.message)
    except Exception as err:
        log_error(err if isinstance(err, Exception) else RuntimeError(str(err)))
        return CliCommandResult(False, str(err))


async def disable_plugin_cli(
    plugin: str,
    scope: InstallableScope | None = None,
) -> CliCommandResult:
    try:
        result = await operations.disable_plugin(plugin, scope)
        if not result.success:
            return CliCommandResult(False, result.message)
        return CliCommandResult(True, result.message)
    except Exception as err:
        log_error(err if isinstance(err, Exception) else RuntimeError(str(err)))
        return CliCommandResult(False, str(err))


async def update_plugin_cli(
    plugin: str,
    scope: PluginScope | None = None,
) -> CliCommandResult:
    try:
        result = await operations.update_plugin(plugin, scope)
        if not result.success:
            return CliCommandResult(False, result.message)
        return CliCommandResult(True, result.message)
    except Exception as err:
        log_error(err if isinstance(err, Exception) else RuntimeError(str(err)))
        return CliCommandResult(False, str(err))


__all__ = [
    "CliCommandResult",
    "install_plugin_cli",
    "uninstall_plugin_cli",
    "enable_plugin_cli",
    "disable_plugin_cli",
    "update_plugin_cli",
]
