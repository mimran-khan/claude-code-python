"""
Plugin policy checks backed by managed settings (policySettings).

Migrated from: utils/plugins/pluginPolicy.ts

Leaf module: only imports settings to avoid circular dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..settings.settings import get_settings_for_source


@dataclass(frozen=True)
class PolicySettingsView:
    """Read-only slice of policy settings relevant to plugins (for testing/introspection)."""

    enabled_plugins: dict[str, bool | None] | None


def read_policy_plugin_settings() -> PolicySettingsView:
    policy = get_settings_for_source("policySettings") or {}
    raw = policy.get("enabledPlugins")
    ep = raw if isinstance(raw, dict) else None
    return PolicySettingsView(enabled_plugins=ep)


def is_plugin_blocked_by_policy(plugin_id: str) -> bool:
    """
    True when org policy force-disables this plugin (enabledPlugins[pluginId] === false).
    """
    view = read_policy_plugin_settings()
    if view.enabled_plugins is None:
        return False
    return view.enabled_plugins.get(plugin_id) is False


def is_plugin_install_allowed(plugin_id: str, _scope: str) -> bool:
    """True when policy does not force-disable the plugin (install/enable chokepoint)."""
    return not is_plugin_blocked_by_policy(plugin_id)


__all__ = [
    "PolicySettingsView",
    "is_plugin_blocked_by_policy",
    "is_plugin_install_allowed",
    "read_policy_plugin_settings",
]
