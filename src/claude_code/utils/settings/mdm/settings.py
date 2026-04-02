"""Parsed MDM settings cache. Migrated from: utils/settings/mdm/settings.ts"""

from __future__ import annotations

from typing import Any

_cache: dict[str, Any] = {}


def get_mdm_settings_snapshot() -> dict[str, Any]:
    return dict(_cache)


def set_mdm_settings_cache(data: dict[str, Any]) -> None:
    _cache.clear()
    _cache.update(data)
