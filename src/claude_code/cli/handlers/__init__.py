"""CLI subcommand handlers migrated from cli/handlers/*.ts."""

from .agents import agents_handler
from .auth import auth_login, auth_logout, auth_status, install_oauth_tokens
from .auto_mode import (
    auto_mode_config_handler,
    auto_mode_critique_handler,
    auto_mode_defaults_handler,
)
from .plugins import (
    VALID_INSTALLABLE_SCOPES,
    VALID_UPDATE_SCOPES,
    handle_marketplace_error,
    marketplace_add_handler,
    marketplace_list_handler,
    marketplace_remove_handler,
    marketplace_update_handler,
    plugin_disable_handler,
    plugin_enable_handler,
    plugin_install_handler,
    plugin_list_handler,
    plugin_uninstall_handler,
    plugin_update_handler,
    plugin_validate_handler,
)

__all__ = [
    "agents_handler",
    "auth_login",
    "auth_logout",
    "auth_status",
    "install_oauth_tokens",
    "auto_mode_defaults_handler",
    "auto_mode_config_handler",
    "auto_mode_critique_handler",
    "VALID_INSTALLABLE_SCOPES",
    "VALID_UPDATE_SCOPES",
    "handle_marketplace_error",
    "marketplace_add_handler",
    "marketplace_list_handler",
    "marketplace_remove_handler",
    "marketplace_update_handler",
    "plugin_disable_handler",
    "plugin_enable_handler",
    "plugin_install_handler",
    "plugin_list_handler",
    "plugin_uninstall_handler",
    "plugin_update_handler",
    "plugin_validate_handler",
]
