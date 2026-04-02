"""
Plugin identifier parsing.

Parse and validate plugin identifiers.

Migrated from: utils/plugins/pluginIdentifier.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SettingSource = Literal["userSettings", "projectSettings", "localSettings", "policySettings"]


@dataclass
class PluginIdentifier:
    """Parsed plugin identifier."""

    name: str
    marketplace: str | None = None
    version: str | None = None

    @property
    def full_id(self) -> str:
        """Get the full plugin ID (name@marketplace)."""
        if self.marketplace:
            return f"{self.name}@{self.marketplace}"
        return self.name


def parse_plugin_identifier(identifier: str) -> PluginIdentifier:
    """
    Parse a plugin identifier string.

    Formats:
    - "plugin-name" - just a name
    - "plugin-name@marketplace" - name with marketplace
    - "plugin-name@marketplace:version" - name with marketplace and version

    Args:
        identifier: The plugin identifier string

    Returns:
        Parsed PluginIdentifier
    """
    version = None
    marketplace = None
    name = identifier

    # Check for version (after :)
    if ":" in identifier:
        parts = identifier.rsplit(":", 1)
        identifier = parts[0]
        version = parts[1] if len(parts) > 1 else None

    # Check for marketplace (after @)
    if "@" in identifier:
        parts = identifier.split("@", 1)
        name = parts[0]
        marketplace = parts[1] if len(parts) > 1 else None
    else:
        name = identifier

    return PluginIdentifier(
        name=name,
        marketplace=marketplace,
        version=version,
    )


def scope_to_setting_source(scope: str) -> SettingSource:
    """
    Convert a plugin scope to a settings source.

    Args:
        scope: Plugin scope (user, project, local, managed)

    Returns:
        Settings source name
    """
    mapping: dict[str, SettingSource] = {
        "user": "userSettings",
        "project": "projectSettings",
        "local": "localSettings",
        "managed": "policySettings",
    }
    return mapping.get(scope, "userSettings")


def setting_source_to_scope(source: SettingSource) -> str:
    """
    Convert a settings source to a plugin scope.

    Args:
        source: Settings source name

    Returns:
        Plugin scope
    """
    mapping = {
        "userSettings": "user",
        "projectSettings": "project",
        "localSettings": "local",
        "policySettings": "managed",
    }
    return mapping.get(source, "user")


def format_plugin_id(name: str, marketplace: str | None = None) -> str:
    """
    Format a plugin ID from name and marketplace.

    Args:
        name: Plugin name
        marketplace: Optional marketplace name

    Returns:
        Formatted plugin ID
    """
    if marketplace:
        return f"{name}@{marketplace}"
    return name


def is_scoped_plugin_id(plugin_id: str) -> bool:
    """
    Check if a plugin ID includes a marketplace scope.

    Args:
        plugin_id: The plugin ID to check

    Returns:
        True if scoped (has @)
    """
    return "@" in plugin_id
