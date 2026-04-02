"""
Plugin Loader.

Handles plugin discovery and loading.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from .types import (
    PluginInfo,
    PluginManifest,
    PluginStatus,
    PluginType,
)

_LOG = structlog.get_logger(__name__)

if TYPE_CHECKING:
    pass


def get_plugins_dir() -> Path:
    """Get the plugins directory.

    Returns:
        Path to the plugins directory
    """
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if config_dir:
        return Path(config_dir) / "plugins"
    return Path.home() / ".claude" / "plugins"


def get_plugin_cache_dir() -> Path:
    """Get the plugin cache directory.

    Returns:
        Path to the plugin cache directory
    """
    return get_plugins_dir() / "cache"


@dataclass
class PluginLoader:
    """Loader for plugins."""

    plugins_dir: Path = field(default_factory=get_plugins_dir)
    _plugins: dict[str, PluginInfo] = field(default_factory=dict)
    _loaded: bool = False
    # plugin_id -> sys.path entries inserted while the plugin is active
    _plugin_sys_path_entries: dict[str, list[str]] = field(default_factory=dict, repr=False)

    def discover(self) -> list[PluginInfo]:
        """Discover installed plugins.

        Returns:
            List of discovered plugins
        """
        plugins: list[PluginInfo] = []

        if not self.plugins_dir.exists():
            return plugins

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Skip cache and hidden directories
            if plugin_dir.name.startswith(".") or plugin_dir.name == "cache":
                continue

            manifest_path = plugin_dir / "plugin.json"
            if not manifest_path.exists():
                # Try package.json
                manifest_path = plugin_dir / "package.json"
                if not manifest_path.exists():
                    continue

            try:
                with open(manifest_path) as f:
                    data = json.load(f)

                manifest = PluginManifest.from_dict(data)

                plugin = PluginInfo(
                    id=plugin_dir.name,
                    manifest=manifest,
                    status="installed",
                    path=str(plugin_dir),
                )

                plugins.append(plugin)
                self._plugins[plugin.id] = plugin

            except (json.JSONDecodeError, OSError) as e:
                _LOG.warning(
                    "plugin_manifest_invalid",
                    plugin_id=plugin_dir.name,
                    manifest_path=str(manifest_path),
                    error_type=type(e).__name__,
                    error=str(e),
                )
                # Create error plugin info
                plugin = PluginInfo(
                    id=plugin_dir.name,
                    manifest=PluginManifest(
                        name=plugin_dir.name,
                        version="unknown",
                    ),
                    status="error",
                    path=str(plugin_dir),
                    error=str(e),
                )
                plugins.append(plugin)
                self._plugins[plugin.id] = plugin

        self._loaded = True
        return plugins

    def get(self, plugin_id: str) -> PluginInfo | None:
        """Get a plugin by ID.

        Args:
            plugin_id: The plugin ID

        Returns:
            The plugin info, or None if not found
        """
        if not self._loaded:
            self.discover()
        return self._plugins.get(plugin_id)

    def list(
        self,
        *,
        status: PluginStatus | None = None,
        plugin_type: PluginType | None = None,
        enabled_only: bool = False,
    ) -> list[PluginInfo]:
        """List plugins with optional filtering.

        Args:
            status: Filter by status
            plugin_type: Filter by type
            enabled_only: Only return enabled plugins

        Returns:
            List of matching plugins
        """
        if not self._loaded:
            self.discover()

        plugins = list(self._plugins.values())

        if status is not None:
            plugins = [p for p in plugins if p.status == status]

        if plugin_type is not None:
            plugins = [
                p
                for p in plugins
                if p.manifest.type == plugin_type
                or (isinstance(p.manifest.type, list) and plugin_type in p.manifest.type)
            ]

        if enabled_only:
            plugins = [p for p in plugins if p.is_enabled]

        return plugins

    async def load(self, plugin_id: str) -> PluginInfo:
        """Load a plugin.

        Args:
            plugin_id: The plugin ID

        Returns:
            The loaded plugin info

        Raises:
            ValueError: If plugin not found
        """
        plugin = self.get(plugin_id)
        if plugin is None:
            raise ValueError(f"Plugin not found: {plugin_id}")

        if plugin.status == "error":
            return plugin

        plugin.status = "loading"

        try:
            self._mount_plugin_path(plugin)
            plugin.status = "active"

        except Exception as e:
            _LOG.warning(
                "plugin_load_failed",
                plugin_id=plugin_id,
                error_type=type(e).__name__,
                error=str(e),
            )
            self._unmount_plugin_path(plugin_id)
            plugin.status = "error"
            plugin.error = str(e)

        return plugin

    async def unload(self, plugin_id: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_id: The plugin ID

        Returns:
            True if plugin was unloaded
        """
        plugin = self.get(plugin_id)
        if plugin is None:
            return False

        if plugin.status != "active":
            return False

        try:
            self._unmount_plugin_path(plugin_id)
            plugin.status = "installed"
            return True

        except Exception as e:
            _LOG.warning(
                "plugin_unload_failed",
                plugin_id=plugin_id,
                error_type=type(e).__name__,
                error=str(e),
            )
            plugin.error = str(e)
            return False

    def _mount_plugin_path(self, plugin: PluginInfo) -> None:
        """Expose the plugin root on ``sys.path`` so Python hooks/commands can import."""
        root = str(Path(plugin.path).resolve())
        if plugin.id in self._plugin_sys_path_entries:
            return
        inserted: list[str] = []
        if root not in sys.path:
            sys.path.insert(0, root)
            inserted.append(root)
        # Optional nested src/ layout (common for Node-style repos)
        src = Path(root) / "src"
        if src.is_dir():
            src_s = str(src.resolve())
            if src_s not in sys.path:
                sys.path.insert(0, src_s)
                inserted.append(src_s)
        self._plugin_sys_path_entries[plugin.id] = inserted

    def _unmount_plugin_path(self, plugin_id: str) -> None:
        for path in self._plugin_sys_path_entries.pop(plugin_id, []):
            try:
                while path in sys.path:
                    sys.path.remove(path)
            except ValueError:
                continue

    def enable(self, plugin_id: str) -> bool:
        """Enable a plugin.

        Args:
            plugin_id: The plugin ID

        Returns:
            True if plugin was enabled
        """
        plugin = self.get(plugin_id)
        if plugin is None:
            return False

        plugin.config.enabled = True
        return True

    def disable(self, plugin_id: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_id: The plugin ID

        Returns:
            True if plugin was disabled
        """
        plugin = self.get(plugin_id)
        if plugin is None:
            return False

        plugin.config.enabled = False
        return True


# Global plugin loader
_default_loader: PluginLoader | None = None


def get_default_loader() -> PluginLoader:
    """Get the default plugin loader."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PluginLoader()
    return _default_loader


def discover_plugins(
    *,
    loader: PluginLoader | None = None,
) -> list[PluginInfo]:
    """Discover installed plugins."""
    if loader is None:
        loader = get_default_loader()
    return loader.discover()


def get_plugin(
    plugin_id: str,
    *,
    loader: PluginLoader | None = None,
) -> PluginInfo | None:
    """Get a plugin by ID."""
    if loader is None:
        loader = get_default_loader()
    return loader.get(plugin_id)


async def load_plugin(
    plugin_id: str,
    *,
    loader: PluginLoader | None = None,
) -> PluginInfo:
    """Load a plugin."""
    if loader is None:
        loader = get_default_loader()
    return await loader.load(plugin_id)
