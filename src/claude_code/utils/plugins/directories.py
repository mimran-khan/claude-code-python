"""
Plugin directories.

Directory management for plugins.

Migrated from: utils/plugins/pluginDirectories.ts
"""

from __future__ import annotations

import os
import shutil

from .plugin_directories import get_plugins_directory


def get_plugin_base_dir() -> str:
    """Get the base directory for all plugin data (respects env / cowork layout)."""
    return get_plugins_directory()


def get_plugin_cache_dir() -> str:
    """Get the directory for cached plugin installations."""
    return os.path.join(get_plugin_base_dir(), "cache")


def get_plugin_data_dir(plugin_id: str) -> str:
    """
    Get the data directory for a specific plugin.

    Args:
        plugin_id: The plugin identifier

    Returns:
        Path to the plugin's data directory
    """
    return os.path.join(get_plugin_base_dir(), "data", plugin_id)


def get_plugin_versioned_cache_path(plugin_id: str, version: str) -> str:
    """
    Get the versioned cache path for a plugin.

    Args:
        plugin_id: The plugin identifier
        version: The plugin version

    Returns:
        Path to the versioned cache directory
    """
    return os.path.join(get_plugin_cache_dir(), f"{plugin_id}@{version}")


def ensure_plugin_dir(path: str) -> str:
    """
    Ensure a plugin directory exists.

    Args:
        path: The directory path

    Returns:
        The path (created if needed)
    """
    os.makedirs(path, exist_ok=True)
    return path


def delete_plugin_data_dir(plugin_id: str) -> bool:
    """
    Delete a plugin's data directory.

    Args:
        plugin_id: The plugin identifier

    Returns:
        True if deleted, False if not found
    """
    data_dir = get_plugin_data_dir(plugin_id)

    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
        return True

    return False


def delete_plugin_cache(plugin_id: str, version: str | None = None) -> bool:
    """
    Delete a plugin's cache.

    Args:
        plugin_id: The plugin identifier
        version: Optional specific version to delete

    Returns:
        True if deleted, False if not found
    """
    if version:
        cache_path = get_plugin_versioned_cache_path(plugin_id, version)
    else:
        cache_path = os.path.join(get_plugin_cache_dir(), plugin_id)

    if os.path.exists(cache_path):
        shutil.rmtree(cache_path)
        return True

    return False


def get_marketplace_cache_dir(marketplace_name: str) -> str:
    """
    Get the cache directory for a marketplace.

    Args:
        marketplace_name: The marketplace name

    Returns:
        Path to the marketplace cache directory
    """
    return os.path.join(get_plugin_base_dir(), "marketplaces", marketplace_name)
