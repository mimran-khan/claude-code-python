"""
Core plugin operations.

Install, uninstall, enable, disable, and update plugins.

Migrated from: services/plugins/pluginOperations.ts (1089 lines) - Core types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# Valid installable scopes (excludes 'managed')
VALID_INSTALLABLE_SCOPES = ["user", "project", "local"]

# Valid scopes for update operations (includes 'managed')
VALID_UPDATE_SCOPES = ["user", "project", "local", "managed"]

# Type aliases
InstallableScope = Literal["user", "project", "local"]
PluginScope = Literal["user", "project", "local", "managed"]


@dataclass
class PluginOperationResult:
    """Result of a plugin operation."""

    success: bool
    message: str
    plugin_id: str | None = None
    plugin_name: str | None = None
    scope: PluginScope | None = None
    reverse_dependents: list[str] = field(default_factory=list)


@dataclass
class PluginUpdateResult:
    """Result of a plugin update operation."""

    success: bool
    message: str
    plugin_id: str | None = None
    new_version: str | None = None
    old_version: str | None = None
    already_up_to_date: bool = False
    scope: PluginScope | None = None


def assert_installable_scope(scope: str) -> None:
    """
    Assert that a scope is a valid installable scope.

    Raises:
        ValueError: If scope is not valid
    """
    if scope not in VALID_INSTALLABLE_SCOPES:
        raise ValueError(f'Invalid scope "{scope}". Must be one of: {", ".join(VALID_INSTALLABLE_SCOPES)}')


def is_installable_scope(scope: str) -> bool:
    """
    Check if a scope is an installable scope (not 'managed').

    Use this for type narrowing in conditional blocks.
    """
    return scope in VALID_INSTALLABLE_SCOPES


def get_project_path_for_scope(scope: str) -> str | None:
    """
    Get the project path for scopes that are project-specific.

    Returns the original cwd for 'project' and 'local' scopes.
    """
    from ...utils.cwd import get_cwd

    if scope in ("project", "local"):
        return get_cwd()
    return None


def is_plugin_enabled_at_project_scope(plugin_id: str) -> bool:
    """
    Check if this plugin is enabled in project settings.

    This is distinct from where a plugin was installed from - a user-scope
    install can also be enabled at project scope via settings.
    """
    from ...utils.settings import get_settings_for_source

    settings = get_settings_for_source("projectSettings")
    if not settings:
        return False

    enabled_plugins = settings.get("enabledPlugins", {})
    return enabled_plugins.get(plugin_id) is True


def scope_to_setting_source(scope: str) -> str:
    """Convert a plugin scope to a settings source."""
    mapping = {
        "user": "userSettings",
        "project": "projectSettings",
        "local": "localSettings",
        "managed": "policySettings",
    }
    return mapping.get(scope, "userSettings")


async def install_plugin(
    plugin_identifier: str,
    scope: InstallableScope = "user",
    force: bool = False,
) -> PluginOperationResult:
    """
    Install a plugin.

    Args:
        plugin_identifier: Plugin ID or marketplace/plugin format
        scope: Installation scope
        force: Force reinstall even if already installed

    Returns:
        PluginOperationResult indicating success/failure
    """
    assert_installable_scope(scope)

    # Stub implementation
    return PluginOperationResult(
        success=False,
        message="Plugin installation not implemented",
    )


async def uninstall_plugin(
    plugin_identifier: str,
    scope: InstallableScope | None = None,
    force: bool = False,
) -> PluginOperationResult:
    """
    Uninstall a plugin.

    Args:
        plugin_identifier: Plugin ID
        scope: Uninstallation scope (auto-detected if not provided)
        force: Force uninstall even with dependents

    Returns:
        PluginOperationResult indicating success/failure
    """
    # Stub implementation
    return PluginOperationResult(
        success=False,
        message="Plugin uninstallation not implemented",
    )


async def enable_plugin(
    plugin_identifier: str,
    scope: InstallableScope = "user",
) -> PluginOperationResult:
    """
    Enable a plugin.

    Args:
        plugin_identifier: Plugin ID
        scope: Settings scope to enable in

    Returns:
        PluginOperationResult indicating success/failure
    """
    assert_installable_scope(scope)

    # Stub implementation
    return PluginOperationResult(
        success=False,
        message="Plugin enabling not implemented",
    )


async def disable_plugin(
    plugin_identifier: str,
    scope: InstallableScope | None = None,
) -> PluginOperationResult:
    """
    Disable a plugin.

    Args:
        plugin_identifier: Plugin ID
        scope: Settings scope (auto-detected if not provided)

    Returns:
        PluginOperationResult indicating success/failure
    """
    # Stub implementation
    return PluginOperationResult(
        success=False,
        message="Plugin disabling not implemented",
    )


async def update_plugin(
    plugin_identifier: str,
    scope: PluginScope | None = None,
) -> PluginUpdateResult:
    """
    Update a plugin to the latest version.

    Args:
        plugin_identifier: Plugin ID
        scope: Update scope (auto-detected if not provided)

    Returns:
        PluginUpdateResult indicating success/failure
    """
    # Stub implementation
    return PluginUpdateResult(
        success=False,
        message="Plugin update not implemented",
    )
