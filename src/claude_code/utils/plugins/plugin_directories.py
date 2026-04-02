"""
Centralized plugin directory configuration.

Migrated from: utils/plugins/pluginDirectories.ts
"""

from __future__ import annotations

import os
import re
import shutil

from ...bootstrap.state import get_use_cowork_plugins
from ..env_utils import get_claude_config_home_dir, is_env_truthy
from ..permissions.path_validation import expand_tilde

PLUGINS_DIR = "plugins"
COWORK_PLUGINS_DIR = "cowork_plugins"


def _plugins_directory_name() -> str:
    if get_use_cowork_plugins():
        return COWORK_PLUGINS_DIR
    if is_env_truthy(os.environ.get("CLAUDE_CODE_USE_COWORK_PLUGINS")):
        return COWORK_PLUGINS_DIR
    return PLUGINS_DIR


def get_plugins_directory() -> str:
    """
    Full path to the plugins root (~/.claude/plugins or env override).

    CLAUDE_CODE_PLUGIN_CACHE_DIR overrides the default layout.
    """
    env_override = os.environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR")
    if env_override:
        return expand_tilde(env_override)
    return os.path.join(get_claude_config_home_dir(), _plugins_directory_name())


def get_plugin_cache_path() -> str:
    """Versioned install cache root: ``<plugins>/cache``."""
    return os.path.join(get_plugins_directory(), "cache")


def get_plugin_seed_dirs() -> list[str]:
    """PATH-like list of read-only seed directories (CLAUDE_CODE_PLUGIN_SEED_DIR)."""
    raw = os.environ.get("CLAUDE_CODE_PLUGIN_SEED_DIR")
    if not raw:
        return []
    return [expand_tilde(p) for p in raw.split(os.pathsep) if p.strip()]


def _sanitize_plugin_id(plugin_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\-_]", "-", plugin_id)


def plugin_data_dir_path(plugin_id: str) -> str:
    """Pure path for per-plugin data (no mkdir)."""
    return os.path.join(get_plugins_directory(), "data", _sanitize_plugin_id(plugin_id))


def get_plugin_data_dir(plugin_id: str) -> str:
    """
    Persistent per-plugin data directory (${CLAUDE_PLUGIN_DATA}).
    Creates the directory on call (mirrors TS sync mkdir).
    """
    directory = plugin_data_dir_path(plugin_id)
    os.makedirs(directory, exist_ok=True)
    return directory


def ensure_plugins_root_exists() -> str:
    """Ensure base plugins directory exists; returns get_plugins_directory()."""
    root = get_plugins_directory()
    os.makedirs(root, exist_ok=True)
    return root


def remove_plugin_tree(path: str) -> None:
    """Best-effort recursive delete (install/uninstall helpers)."""
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
