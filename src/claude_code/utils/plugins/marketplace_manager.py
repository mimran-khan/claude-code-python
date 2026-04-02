"""
Marketplace configuration and plugin resolution.

Migrated from: utils/plugins/marketplaceManager.ts (expanded port).
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..debug import log_for_debugging
from ..settings.settings import get_merged_settings
from .dir_settings import get_add_dir_enabled_plugins, get_add_dir_extra_marketplaces
from .official_marketplace import OFFICIAL_MARKETPLACE_NAME, OFFICIAL_MARKETPLACE_SOURCE
from .plugin_directories import get_plugin_seed_dirs, get_plugins_directory
from .plugin_identifier import parse_plugin_identifier

KnownMarketplacesFile = dict[str, Any]

_marketplace_object_cache: dict[str, dict[str, Any]] = {}


@dataclass
class DeclaredMarketplace:
    source: dict[str, Any]
    source_is_fallback: bool = False


@dataclass
class AddMarketplaceResult:
    name: str = ""
    already_materialized: bool = True
    resolved_source: dict[str, Any] = field(default_factory=dict)


def _known_marketplaces_path() -> str:
    return os.path.join(get_plugins_directory(), "known_marketplaces.json")


def get_marketplaces_cache_dir() -> str:
    return os.path.join(get_plugins_directory(), "marketplaces")


def clear_marketplaces_cache() -> None:
    """Clear in-memory marketplace JSON cache (mirrors TS memo clear)."""
    _marketplace_object_cache.clear()


def _normalize_declared_entry(raw: Any) -> DeclaredMarketplace | None:
    if raw is False:
        return None
    if not isinstance(raw, dict):
        return None
    src = raw.get("source")
    if not isinstance(src, dict):
        return None
    return DeclaredMarketplace(
        source=dict(src),
        source_is_fallback=bool(raw.get("sourceIsFallback")),
    )


def get_declared_marketplaces() -> dict[str, DeclaredMarketplace]:
    implicit: dict[str, DeclaredMarketplace] = {}
    merged = get_merged_settings()
    enabled = {**get_add_dir_enabled_plugins(), **(merged.get("enabledPlugins") or {})}
    for plugin_id, value in enabled.items():
        if value:
            parsed = parse_plugin_identifier(plugin_id)
            if parsed.marketplace == OFFICIAL_MARKETPLACE_NAME:
                implicit[OFFICIAL_MARKETPLACE_NAME] = DeclaredMarketplace(
                    source=dict(OFFICIAL_MARKETPLACE_SOURCE),
                    source_is_fallback=True,
                )
                break

    extra_merged = {
        **get_add_dir_extra_marketplaces(),
        **(merged.get("extraKnownMarketplaces") or {}),
    }
    explicit: dict[str, DeclaredMarketplace] = {}
    for name, raw in extra_merged.items():
        dm = _normalize_declared_entry(raw)
        if dm is not None:
            explicit[str(name)] = dm

    return {**implicit, **explicit}


async def load_known_marketplaces_config_safe() -> KnownMarketplacesFile:
    path = _known_marketplaces_path()

    def _read() -> KnownMarketplacesFile:
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError) as exc:
            log_for_debugging(f"known_marketplaces.json: {exc}")
            return {}

    return await asyncio.to_thread(_read)


async def load_known_marketplaces_config() -> KnownMarketplacesFile:
    return await load_known_marketplaces_config_safe()


async def save_known_marketplaces_config(config: KnownMarketplacesFile) -> None:
    path = _known_marketplaces_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    clear_marketplaces_cache()

    def _write() -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)

    await asyncio.to_thread(_write)


async def _read_seed_known_marketplaces(seed_dir: str) -> KnownMarketplacesFile | None:
    seed_json = os.path.join(seed_dir, "known_marketplaces.json")

    def _read() -> KnownMarketplacesFile | None:
        try:
            with open(seed_json, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            log_for_debugging(
                f"Seed known_marketplaces.json invalid at {seed_dir}: {exc}",
                level="warn",
            )
            return None
        return data if isinstance(data, dict) else None

    return await asyncio.to_thread(_read)


async def _find_seed_marketplace_location(seed_dir: str, name: str) -> str | None:
    dir_candidate = os.path.join(seed_dir, "marketplaces", name)
    json_candidate = os.path.join(seed_dir, "marketplaces", f"{name}.json")

    def _exists(path: str) -> bool:
        return os.path.isdir(path) or os.path.isfile(path)

    for candidate in (dir_candidate, json_candidate):
        if await asyncio.to_thread(_exists, candidate):
            return candidate
    return None


def _entries_equivalent(existing: Any, desired: dict[str, Any]) -> bool:
    if not isinstance(existing, dict):
        return False
    return (
        existing.get("installLocation") == desired.get("installLocation")
        and existing.get("source") == desired.get("source")
        and existing.get("autoUpdate") == desired.get("autoUpdate")
    )


async def register_seed_marketplaces() -> bool:
    seed_dirs = get_plugin_seed_dirs()
    if not seed_dirs:
        return False

    primary = await load_known_marketplaces_config()
    claimed: set[str] = set()
    changed = 0

    for seed_dir in seed_dirs:
        seed_config = await _read_seed_known_marketplaces(seed_dir)
        if not seed_config:
            continue
        for name, seed_entry in seed_config.items():
            if name in claimed:
                continue
            resolved_location = await _find_seed_marketplace_location(seed_dir, name)
            if not resolved_location:
                log_for_debugging(
                    f"Seed marketplace '{name}' not found under {seed_dir}/marketplaces/, skipping",
                    level="warn",
                )
                continue
            claimed.add(name)
            if not isinstance(seed_entry, dict):
                continue
            src = seed_entry.get("source")
            if not isinstance(src, dict):
                continue
            desired: dict[str, Any] = {
                "source": dict(src),
                "installLocation": resolved_location,
                "lastUpdated": seed_entry.get("lastUpdated"),
                "autoUpdate": False,
            }
            if _entries_equivalent(primary.get(name), desired):
                continue
            primary[name] = desired
            changed += 1

    if changed > 0:
        await save_known_marketplaces_config(primary)
        log_for_debugging(f"Synced {changed} marketplace(s) from seed dir(s)")
        return True
    return False


async def get_marketplace(marketplace_name: str) -> dict[str, Any] | None:
    cached = _marketplace_object_cache.get(marketplace_name)
    if cached is not None:
        return cached

    known = await load_known_marketplaces_config_safe()
    entry = known.get(marketplace_name)
    if not isinstance(entry, dict):
        return None
    loc = entry.get("installLocation")
    if not isinstance(loc, str):
        return None

    candidates = [
        os.path.join(loc, ".claude-plugin", "marketplace.json"),
        os.path.join(loc, "marketplace.json"),
        loc if loc.endswith(".json") else "",
    ]

    def _read_path(path: str) -> dict[str, Any] | None:
        if not path:
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    data: dict[str, Any] | None = None
    for candidate in candidates:
        if not candidate:
            continue
        data = await asyncio.to_thread(_read_path, candidate)
        if data is not None:
            break
    if data is None:
        return None
    _marketplace_object_cache[marketplace_name] = data
    return data


async def get_plugin_by_id(plugin_id: str) -> dict[str, Any] | None:
    parsed = parse_plugin_identifier(plugin_id)
    if not parsed.marketplace or not parsed.name:
        return None
    marketplace = await get_marketplace(parsed.marketplace)
    if not marketplace:
        return None
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        return None
    for p in plugins:
        if isinstance(p, dict) and p.get("name") == parsed.name:
            return {"entry": p}
    return None


async def load_plugins_from_marketplaces(*, cache_only: bool) -> tuple[list[Any], list[Any]]:
    """
    Load plugins from materialized marketplaces.

    Stub: returns no plugins until marketplace install pipeline is wired.
    """
    del cache_only
    return [], []


async def get_marketplace_cache_only(name: str) -> Any | None:
    return await get_marketplace(name)


async def get_plugin_by_id_cache_only(plugin_id: str) -> Any | None:
    return await get_plugin_by_id(plugin_id)


async def add_marketplace_source(
    source: dict[str, Any],
    _on_progress: Callable[..., None] | None = None,
) -> AddMarketplaceResult:
    """Placeholder for marketplace install; extend with clone/fetch logic."""
    del _on_progress
    return AddMarketplaceResult(
        name=str(source.get("name", "")),
        already_materialized=True,
        resolved_source=dict(source),
    )


__all__ = [
    "AddMarketplaceResult",
    "DeclaredMarketplace",
    "KnownMarketplacesFile",
    "add_marketplace_source",
    "clear_marketplaces_cache",
    "get_declared_marketplaces",
    "get_marketplace",
    "get_marketplace_cache_only",
    "get_marketplaces_cache_dir",
    "get_plugin_by_id",
    "get_plugin_by_id_cache_only",
    "load_known_marketplaces_config",
    "load_known_marketplaces_config_safe",
    "load_plugins_from_marketplaces",
    "register_seed_marketplaces",
    "save_known_marketplaces_config",
]
