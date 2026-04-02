"""
Zip-cache metadata I/O for plugin marketplaces.

Migrated from: utils/plugins/zipCacheAdapters.ts
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from ..debug import log_for_debugging
from ..slow_operations import json_stringify
from .marketplace_manager import load_known_marketplaces_config_safe
from .zip_cache import (
    atomic_write_to_zip_cache,
    get_marketplace_json_relative_path,
    get_plugin_zip_cache_path,
    get_zip_cache_known_marketplaces_path,
)

KnownMarketplacesFile = dict[str, Any]


async def read_zip_cache_known_marketplaces() -> KnownMarketplacesFile:
    path = get_zip_cache_known_marketplaces_path()

    def _read() -> KnownMarketplacesFile:
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError) as exc:
            log_for_debugging(
                f"Invalid known_marketplaces.json in zip cache: {exc}",
                level="error",
            )
            return {}

    return await asyncio.to_thread(_read)


async def write_zip_cache_known_marketplaces(data: KnownMarketplacesFile) -> None:
    await atomic_write_to_zip_cache(
        get_zip_cache_known_marketplaces_path(),
        json_stringify(data, indent=2),
    )


async def read_marketplace_json(marketplace_name: str) -> dict[str, Any] | None:
    zip_cache_path = get_plugin_zip_cache_path()
    if not zip_cache_path:
        return None
    rel = get_marketplace_json_relative_path(marketplace_name)
    full_path = os.path.join(zip_cache_path, rel)

    def _read() -> dict[str, Any] | None:
        try:
            with open(full_path, encoding="utf-8") as handle:
                parsed = json.load(handle)
            return parsed if isinstance(parsed, dict) else None
        except (OSError, json.JSONDecodeError) as exc:
            log_for_debugging(f"Invalid marketplace JSON for {marketplace_name}: {exc}")
            return None

    return await asyncio.to_thread(_read)


async def save_marketplace_json_to_zip_cache(
    marketplace_name: str,
    install_location: str,
) -> None:
    zip_cache_path = get_plugin_zip_cache_path()
    if not zip_cache_path:
        return
    content = await _read_marketplace_json_content(install_location)
    if content is None:
        return
    rel = get_marketplace_json_relative_path(marketplace_name)
    await atomic_write_to_zip_cache(os.path.join(zip_cache_path, rel), content)


async def _read_marketplace_json_content(dir_or_file: str) -> str | None:
    candidates = [
        os.path.join(dir_or_file, ".claude-plugin", "marketplace.json"),
        os.path.join(dir_or_file, "marketplace.json"),
        dir_or_file,
    ]

    def _try_read() -> str | None:
        for candidate in candidates:
            try:
                with open(candidate, encoding="utf-8") as handle:
                    return handle.read()
            except OSError:
                continue
        return None

    return await asyncio.to_thread(_try_read)


async def sync_marketplaces_to_zip_cache() -> None:
    known_marketplaces = await load_known_marketplaces_config_safe()
    for name, entry in known_marketplaces.items():
        if not isinstance(entry, dict):
            continue
        loc = entry.get("installLocation")
        if not isinstance(loc, str):
            continue
        try:
            await save_marketplace_json_to_zip_cache(name, loc)
        except OSError as exc:
            log_for_debugging(f"Failed to save marketplace JSON for {name}: {exc}")

    zip_cached = await read_zip_cache_known_marketplaces()
    merged: KnownMarketplacesFile = {**zip_cached, **known_marketplaces}
    await write_zip_cache_known_marketplaces(merged)


__all__ = [
    "read_marketplace_json",
    "read_zip_cache_known_marketplaces",
    "save_marketplace_json_to_zip_cache",
    "sync_marketplaces_to_zip_cache",
    "write_zip_cache_known_marketplaces",
]
