"""
Managed (policy) plugin names from settings.

Migrated from: utils/plugins/managedPlugins.ts (minimal port).
"""

from __future__ import annotations

from ..settings.settings import get_settings_for_source


def get_managed_plugin_names() -> set[str]:
    """
    Plugin name prefixes governed by policySettings.enabledPlugins.

    Returns empty set until settings layer exposes the full structure.
    """
    policy = get_settings_for_source("policySettings") or {}
    enabled = policy.get("enabledPlugins")
    if not isinstance(enabled, dict):
        return set()
    names: set[str] = set()
    for key in enabled:
        if isinstance(key, str) and key:
            names.add(key.split("@", 1)[0])
    return names


__all__ = ["get_managed_plugin_names"]
