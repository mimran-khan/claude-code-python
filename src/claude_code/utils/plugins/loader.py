"""
Plugin loader.

Load and cache plugin manifests.

Migrated from: utils/plugins/pluginLoader.ts
"""

from __future__ import annotations

import json
import os

from .schemas import PluginManifest

# Plugin cache
_plugin_cache: dict[str, PluginManifest] = {}
_cache_reason: str | None = None


def clear_plugin_cache(reason: str = "manual") -> None:
    """
    Clear the plugin cache.

    Args:
        reason: Reason for clearing the cache
    """
    global _plugin_cache, _cache_reason
    _plugin_cache = {}
    _cache_reason = reason


def load_plugin_manifest(plugin_path: str) -> PluginManifest | None:
    """
    Load a plugin manifest from disk.

    Args:
        plugin_path: Path to the plugin directory

    Returns:
        PluginManifest if found and valid, None otherwise
    """
    manifest_path = os.path.join(plugin_path, "plugin.json")

    if not os.path.exists(manifest_path):
        # Try package.json as fallback
        manifest_path = os.path.join(plugin_path, "package.json")
        if not os.path.exists(manifest_path):
            return None

    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)

        return PluginManifest(
            name=data.get("name", ""),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            author=data.get("author"),
            license=data.get("license"),
            homepage=data.get("homepage"),
            repository=data.get("repository"),
            main=data.get("main"),
            engines=data.get("engines", {}),
            dependencies=data.get("dependencies", {}),
            permissions=data.get("permissions", []),
            tools=data.get("tools", []),
            commands=data.get("commands", []),
            hooks=data.get("hooks", []),
        )
    except (json.JSONDecodeError, OSError):
        return None


def load_all_plugins() -> list[PluginManifest]:
    """
    Load all installed plugins.

    Returns:
        List of PluginManifest objects
    """
    plugins = []

    # Get plugin directories
    from .directories import get_plugin_cache_dir

    cache_dir = get_plugin_cache_dir()
    if not os.path.exists(cache_dir):
        return plugins

    # Scan for plugins
    for name in os.listdir(cache_dir):
        plugin_path = os.path.join(cache_dir, name)
        if os.path.isdir(plugin_path):
            manifest = load_plugin_manifest(plugin_path)
            if manifest:
                plugins.append(manifest)

    return plugins


def get_cached_plugin(plugin_id: str) -> PluginManifest | None:
    """
    Get a plugin from cache.

    Args:
        plugin_id: The plugin identifier

    Returns:
        Cached PluginManifest or None
    """
    return _plugin_cache.get(plugin_id)


def cache_plugin(plugin_id: str, manifest: PluginManifest) -> None:
    """
    Cache a plugin manifest.

    Args:
        plugin_id: The plugin identifier
        manifest: The plugin manifest
    """
    _plugin_cache[plugin_id] = manifest
