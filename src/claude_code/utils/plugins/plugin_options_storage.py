"""
Per-plugin user option storage (${user_config.*} substitution).

Migrated from: utils/plugins/pluginOptionsStorage.ts (minimal port).
"""

from __future__ import annotations

import json
import os
from typing import Any

from .plugin_directories import get_plugins_directory

_options_cache: dict[str, dict[str, Any]] = {}


def clear_plugin_options_cache() -> None:
    global _options_cache
    _options_cache = {}


def get_plugin_storage_id(repository: str) -> str:
    return repository.replace("/", "_").replace("@", "_")


def _options_path(repository: str) -> str:
    safe = get_plugin_storage_id(repository)
    return os.path.join(get_plugins_directory(), "options", f"{safe}.json")


def load_plugin_options(repository: str) -> dict[str, Any]:
    if repository in _options_cache:
        return _options_cache[repository]
    path = _options_path(repository)
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    _options_cache[repository] = data
    return data


def substitute_plugin_variables(
    text: str,
    *,
    path: str,
    source: str,
) -> str:
    data_dir = os.path.join(get_plugins_directory(), "data")
    return (
        text.replace("${CLAUDE_PLUGIN_ROOT}", path)
        .replace("${CLAUDE_PLUGIN_DATA}", data_dir)
        .replace("${CLAUDE_PLUGIN_SOURCE}", source)
    )


def substitute_user_config_in_content(
    text: str,
    _values: dict[str, Any],
    _schema: dict[str, Any] | None,
) -> str:
    """Placeholder: full TS substitution for sensitive keys not ported yet."""
    return text


def substitute_user_config_variables(
    text: str,
    _values: dict[str, Any],
) -> str:
    return text


__all__ = [
    "clear_plugin_options_cache",
    "get_plugin_storage_id",
    "load_plugin_options",
    "substitute_plugin_variables",
    "substitute_user_config_in_content",
    "substitute_user_config_variables",
]
