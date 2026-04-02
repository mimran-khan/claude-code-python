"""
Plugin services module.

Plugin operations and installation management.

Migrated from: services/plugins/*.ts
"""

from .installation_manager import (
    perform_background_plugin_installations,
)
from .operations import (
    VALID_INSTALLABLE_SCOPES,
    VALID_UPDATE_SCOPES,
    InstallableScope,
    PluginOperationResult,
    PluginUpdateResult,
    assert_installable_scope,
    get_project_path_for_scope,
    is_installable_scope,
    is_plugin_enabled_at_project_scope,
)
from .plugin_cli_commands import (
    CliCommandResult,
    disable_plugin_cli,
    enable_plugin_cli,
    install_plugin_cli,
    uninstall_plugin_cli,
    update_plugin_cli,
)

__all__ = [
    # operations
    "VALID_INSTALLABLE_SCOPES",
    "VALID_UPDATE_SCOPES",
    "InstallableScope",
    "PluginOperationResult",
    "PluginUpdateResult",
    "is_installable_scope",
    "assert_installable_scope",
    "get_project_path_for_scope",
    "is_plugin_enabled_at_project_scope",
    # installation_manager
    "perform_background_plugin_installations",
    # plugin_cli_commands
    "CliCommandResult",
    "disable_plugin_cli",
    "enable_plugin_cli",
    "install_plugin_cli",
    "uninstall_plugin_cli",
    "update_plugin_cli",
]
