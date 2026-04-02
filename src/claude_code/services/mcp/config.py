"""
MCP configuration.

Configuration management for MCP servers.

Migrated from: services/mcp/config.ts
"""

from __future__ import annotations

from typing import Any

from .types import (
    ConfigScope,
    McpServerConfig,
    parse_server_config,
)


def get_mcp_servers(scope: ConfigScope | None = None) -> dict[str, McpServerConfig]:
    """
    Get configured MCP servers.

    Args:
        scope: Optional scope to filter by

    Returns:
        Dict of server name -> config
    """
    from ...utils.settings import get_settings_for_source

    servers: dict[str, McpServerConfig] = {}

    # Determine which sources to check
    sources = []
    if scope is None:
        sources = ["userSettings", "projectSettings", "localSettings"]
    elif scope == "user":
        sources = ["userSettings"]
    elif scope == "project":
        sources = ["projectSettings"]
    elif scope == "local":
        sources = ["localSettings"]

    for source in sources:
        settings = get_settings_for_source(source)
        if not settings:
            continue

        mcp_servers = settings.get("mcpServers", {})
        for name, config_data in mcp_servers.items():
            if name not in servers:
                servers[name] = parse_server_config(config_data)

    return servers


def add_mcp_server(
    name: str,
    config: McpServerConfig | dict[str, Any],
    scope: ConfigScope = "user",
) -> bool:
    """
    Add an MCP server configuration.

    Args:
        name: Server name
        config: Server configuration
        scope: Configuration scope

    Returns:
        True if added successfully
    """
    from ...utils.plugins.identifier import scope_to_setting_source
    from ...utils.settings import update_settings_for_source

    source = scope_to_setting_source(scope)

    # Convert to dict if needed
    if not isinstance(config, dict):
        config_dict = {
            "type": config.type,
        }
        if hasattr(config, "command"):
            config_dict["command"] = config.command
            config_dict["args"] = config.args
            config_dict["env"] = config.env
        elif hasattr(config, "url"):
            config_dict["url"] = config.url
            if hasattr(config, "headers"):
                config_dict["headers"] = config.headers
            oauth_cid = getattr(config, "oauth_client_id", None)
            if oauth_cid:
                config_dict["oauthClientId"] = oauth_cid
    else:
        config_dict = config

    return update_settings_for_source(source, {"mcpServers": {name: config_dict}})


def remove_mcp_server(
    name: str,
    scope: ConfigScope = "user",
) -> bool:
    """
    Remove an MCP server configuration.

    Args:
        name: Server name
        scope: Configuration scope

    Returns:
        True if removed successfully
    """
    from ...utils.plugins.identifier import scope_to_setting_source
    from ...utils.settings import get_settings_for_source, update_settings_for_source

    source = scope_to_setting_source(scope)

    settings = get_settings_for_source(source)
    if not settings:
        return False

    mcp_servers = settings.get("mcpServers", {})
    if name not in mcp_servers:
        return False

    del mcp_servers[name]

    return update_settings_for_source(source, {"mcpServers": mcp_servers})


def validate_mcp_config(config: dict[str, Any]) -> list[str]:
    """
    Validate an MCP server configuration.

    Args:
        config: Configuration to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    config_type = config.get("type", "stdio")

    if config_type == "stdio":
        if not config.get("command"):
            errors.append("Stdio config requires 'command' field")

    elif config_type in ("sse", "http", "ws"):
        if not config.get("url"):
            errors.append(f"{config_type} config requires 'url' field")

    elif config_type == "sdk":
        if not config.get("name"):
            errors.append("SDK config requires 'name' field")

    else:
        errors.append(f"Unknown transport type: {config_type}")

    return errors
