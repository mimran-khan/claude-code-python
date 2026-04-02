"""
Delisted plugin detection and auto-uninstall.

Migrated from: utils/plugins/pluginBlocklist.ts
"""

from __future__ import annotations

from typing import Any

from claude_code.services.plugins.operations import uninstall_plugin

from ..debug import log_for_debugging
from ..errors import error_message
from .installed_manager import load_installed_plugins_v2
from .marketplace_manager import get_marketplace, load_known_marketplaces_config_safe
from .plugin_flagging import add_flagged_plugin, get_flagged_plugins, load_flagged_plugins


def detect_delisted_plugins(
    installed_plugins: dict[str, Any],
    marketplace: dict[str, Any],
    marketplace_name: str,
) -> list[str]:
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        return []
    marketplace_plugin_names = {p.get("name") for p in plugins if isinstance(p, dict)}
    suffix = f"@{marketplace_name}"
    delisted: list[str] = []
    raw_plugins = installed_plugins.get("plugins")
    if not isinstance(raw_plugins, dict):
        return []
    for plugin_id in raw_plugins:
        if not isinstance(plugin_id, str) or not plugin_id.endswith(suffix):
            continue
        plugin_name = plugin_id[: -len(suffix)]
        if plugin_name not in marketplace_plugin_names:
            delisted.append(plugin_id)
    return delisted


async def detect_and_uninstall_delisted_plugins() -> list[str]:
    await load_flagged_plugins()
    installed = load_installed_plugins_v2()
    already_flagged = get_flagged_plugins()
    known = await load_known_marketplaces_config_safe()
    newly_flagged: list[str] = []

    for marketplace_name in list(known.keys()):
        try:
            marketplace = await get_marketplace(marketplace_name)
            if not marketplace:
                continue
            if not marketplace.get("forceRemoveDeletedPlugins"):
                continue
            delisted = detect_delisted_plugins(installed, marketplace, marketplace_name)
            plugins_map = installed.get("plugins")
            if not isinstance(plugins_map, dict):
                continue
            for plugin_id in delisted:
                if plugin_id in already_flagged:
                    continue
                installations = plugins_map.get(plugin_id)
                if not isinstance(installations, list):
                    continue
                has_user_install = any(
                    isinstance(i, dict) and i.get("scope") in ("user", "project", "local") for i in installations
                )
                if not has_user_install:
                    continue
                for installation in installations:
                    if not isinstance(installation, dict):
                        continue
                    scope = installation.get("scope")
                    if scope not in ("user", "project", "local"):
                        continue
                    try:
                        await uninstall_plugin(plugin_id, scope=scope)  # type: ignore[arg-type]
                    except Exception as exc:
                        log_for_debugging(
                            f"Failed to auto-uninstall delisted plugin {plugin_id} from {scope}: {error_message(exc)}",
                            level="error",
                        )
                await add_flagged_plugin(plugin_id)
                newly_flagged.append(plugin_id)
        except Exception as exc:
            log_for_debugging(
                f'Failed to check for delisted plugins in "{marketplace_name}": {error_message(exc)}',
                level="warn",
            )
    return newly_flagged


def is_plugin_blocklisted(plugin_id: str, policy: dict[str, Any] | None = None) -> bool:
    del policy
    return False


__all__ = [
    "detect_and_uninstall_delisted_plugins",
    "detect_delisted_plugins",
    "is_plugin_blocklisted",
]
