"""
Session/disk cache for remote managed settings (leaf module, minimal imports).

Migrated from: services/remoteManagedSettings/syncCacheState.ts
"""

from __future__ import annotations

import json
import os
from typing import Any

from ...utils.config_utils import get_claude_config_dir

SETTINGS_FILENAME = "remote-settings.json"

_session_cache: dict[str, Any] | None = None
_eligible: bool | None = None


def set_session_cache(value: dict[str, Any] | None) -> None:
    global _session_cache
    _session_cache = value


def reset_sync_cache() -> None:
    global _session_cache, _eligible
    _session_cache = None
    _eligible = None


def set_eligibility(v: bool) -> bool:
    global _eligible
    _eligible = v
    return v


def get_settings_path() -> str:
    return os.path.join(get_claude_config_dir(), SETTINGS_FILENAME)


def _load_settings() -> dict[str, Any] | None:
    path = get_settings_path()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def get_remote_managed_settings_sync_from_cache() -> dict[str, Any] | None:
    global _session_cache
    if _eligible is not True:
        return None
    if _session_cache is not None:
        return _session_cache
    cached = _load_settings()
    if cached is not None:
        _session_cache = cached
    return _session_cache
