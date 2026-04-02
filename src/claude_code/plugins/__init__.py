"""
Plugin System.

Manages plugin discovery, loading, and lifecycle.
"""

from .builtin_mode import (
    get_auto_mode_flag_cli,
    is_auto_mode_active,
    is_auto_mode_circuit_broken,
    reset_for_testing,
    set_auto_mode_active,
    set_auto_mode_circuit_broken,
    set_auto_mode_flag_cli,
)
from .bundled_init import init_builtin_plugins
from .loader import (
    PluginLoader,
    discover_plugins,
    get_plugin,
    load_plugin,
)
from .types import (
    PluginConfig,
    PluginInfo,
    PluginManifest,
    PluginStatus,
    PluginType,
)

__all__ = [
    # Types
    "PluginType",
    "PluginStatus",
    "PluginConfig",
    "PluginInfo",
    "PluginManifest",
    # Loader
    "PluginLoader",
    "load_plugin",
    "discover_plugins",
    "get_plugin",
    "init_builtin_plugins",
    "set_auto_mode_active",
    "is_auto_mode_active",
    "set_auto_mode_flag_cli",
    "get_auto_mode_flag_cli",
    "set_auto_mode_circuit_broken",
    "is_auto_mode_circuit_broken",
    "reset_for_testing",
]
