"""Re-export add-dir plugin settings from :mod:`dir_settings`."""

from __future__ import annotations

from .dir_settings import get_add_dir_enabled_plugins, get_add_dir_extra_marketplaces

__all__ = ["get_add_dir_enabled_plugins", "get_add_dir_extra_marketplaces"]
