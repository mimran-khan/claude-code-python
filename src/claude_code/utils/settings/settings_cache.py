"""
Session + per-source settings caches (TS layer alongside ``settings.py`` caches).

Migrated from: utils/settings/settingsCache.ts
"""

from __future__ import annotations

from typing import Any

from .constants import SettingSource
from .validation import ValidationError

_session_settings_cache: dict[str, Any] | None = None
_per_source: dict[SettingSource, dict[str, Any] | None] = {}
_parsed_files: dict[str, tuple[dict[str, Any] | None, list[ValidationError]]] = {}


def get_session_settings_cache() -> dict[str, Any] | None:
    return _session_settings_cache


def set_session_settings_cache(value: dict[str, Any]) -> None:
    global _session_settings_cache
    _session_settings_cache = value


def get_cached_settings_for_source(
    source: SettingSource,
) -> tuple[bool, dict[str, Any] | None]:
    """(hit, value). ``hit`` False => cache miss; ``hit`` True and None => cached empty."""
    if source not in _per_source:
        return False, None
    return True, _per_source[source]


def set_cached_settings_for_source(source: SettingSource, value: dict[str, Any] | None) -> None:
    _per_source[source] = value


def get_cached_parsed_file(
    path: str,
) -> tuple[dict[str, Any] | None, list[ValidationError]] | None:
    return _parsed_files.get(path)


def set_cached_parsed_file(
    path: str,
    value: tuple[dict[str, Any] | None, list[ValidationError]],
) -> None:
    _parsed_files[path] = value


def reset_layered_settings_cache() -> None:
    global _session_settings_cache
    _session_settings_cache = None
    _per_source.clear()
    _parsed_files.clear()
