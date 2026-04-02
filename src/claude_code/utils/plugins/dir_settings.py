"""
Plugin-related settings merged from ``--add-dir`` trees (lowest priority).

Migrated from: utils/plugins/addDirPluginSettings.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from ...bootstrap.state import get_additional_directories_for_claude_md
from ..settings.settings import parse_settings_file

SETTINGS_FILES = ("settings.json", "settings.local.json")


@dataclass
class MergedAddDirPluginSettings:
    """Both add-dir plugin-related maps (lowest precedence vs normal settings)."""

    enabled_plugins: dict[str, Any]
    extra_known_marketplaces: dict[str, Any]


def load_merged_add_dir_plugin_settings() -> MergedAddDirPluginSettings:
    """Return merged enabledPlugins and extraKnownMarketplaces from all add-dir trees."""
    return MergedAddDirPluginSettings(
        enabled_plugins=get_add_dir_enabled_plugins(),
        extra_known_marketplaces=get_add_dir_extra_marketplaces(),
    )


def get_add_dir_enabled_plugins() -> dict[str, Any]:
    """
    Merge ``enabledPlugins`` from each ``<add-dir>/.claude/settings*.json``.

    Later files override earlier within the same dir; later dirs override earlier dirs.
    """
    result: dict[str, Any] = {}
    for base in get_additional_directories_for_claude_md():
        for name in SETTINGS_FILES:
            path = os.path.join(base, ".claude", name)
            settings, _ = parse_settings_file(path)
            ep = settings.get("enabledPlugins") if settings else None
            if isinstance(ep, dict):
                result.update(ep)
    return result


def get_add_dir_extra_marketplaces() -> dict[str, Any]:
    """Merge ``extraKnownMarketplaces`` from add-dir settings (same precedence)."""
    result: dict[str, Any] = {}
    for base in get_additional_directories_for_claude_md():
        for name in SETTINGS_FILES:
            path = os.path.join(base, ".claude", name)
            settings, _ = parse_settings_file(path)
            em = settings.get("extraKnownMarketplaces") if settings else None
            if isinstance(em, dict):
                result.update(em)
    return result


__all__ = [
    "MergedAddDirPluginSettings",
    "get_add_dir_enabled_plugins",
    "get_add_dir_extra_marketplaces",
    "load_merged_add_dir_plugin_settings",
]
