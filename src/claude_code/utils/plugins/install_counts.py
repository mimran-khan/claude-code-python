"""
Plugin install counts cache and GitHub stats fetch.

Migrated from: utils/plugins/installCounts.ts
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from ..debug import log_for_debugging
from ..errors import error_message, get_errno_code
from ..log import log_error
from ..slow_operations import json_stringify
from .fetch_telemetry import classify_fetch_error, log_plugin_fetch
from .plugin_directories import ensure_plugins_root_exists

INSTALL_COUNTS_CACHE_VERSION = 1
INSTALL_COUNTS_CACHE_FILENAME = "install-counts-cache.json"
INSTALL_COUNTS_URL = (
    "https://raw.githubusercontent.com/anthropics/claude-plugins-official/refs/heads/stats/stats/plugin-installs.json"
)
CACHE_TTL_MS = 24 * 60 * 60 * 1000


@dataclass
class InstallCountsCache:
    version: int
    fetched_at: str
    counts: list[dict[str, Any]]


def _cache_path() -> str:
    ensure_plugins_root_exists()
    from .plugin_directories import get_plugins_directory

    return os.path.join(get_plugins_directory(), INSTALL_COUNTS_CACHE_FILENAME)


def _validate_cache(parsed: dict[str, Any]) -> InstallCountsCache | None:
    if not isinstance(parsed, dict):
        return None
    version = parsed.get("version")
    fetched_at = parsed.get("fetchedAt")
    counts = parsed.get("counts")
    if version != INSTALL_COUNTS_CACHE_VERSION:
        log_for_debugging(
            f"Install counts cache version mismatch (got {version}, expected {INSTALL_COUNTS_CACHE_VERSION})",
        )
        return None
    if not isinstance(fetched_at, str) or not isinstance(counts, list):
        log_for_debugging("Install counts cache has invalid structure")
        return None
    try:
        iso = fetched_at.replace("Z", "+00:00") if fetched_at.endswith("Z") else fetched_at
        fetched_ms = int(datetime.fromisoformat(iso).timestamp() * 1000)
    except ValueError:
        log_for_debugging("Install counts cache has invalid fetchedAt timestamp")
        return None
    if time.time() * 1000 - fetched_ms > CACHE_TTL_MS:
        log_for_debugging("Install counts cache is stale (>24h old)")
        return None
    for entry in counts:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("plugin"), str)
            or not isinstance(entry.get("unique_installs"), (int, float))
        ):
            log_for_debugging("Install counts cache has malformed entries")
            return None
    return InstallCountsCache(version=version, fetched_at=fetched_at, counts=counts)


async def _load_install_counts_cache() -> InstallCountsCache | None:
    path = _cache_path()

    def _read() -> InstallCountsCache | None:
        try:
            with open(path, encoding="utf-8") as handle:
                parsed = json.load(handle)
        except OSError as exc:
            code = get_errno_code(exc)
            if code != "ENOENT":
                log_for_debugging(f"Failed to load install counts cache: {error_message(exc)}")
            return None
        except json.JSONDecodeError:
            log_for_debugging("Install counts cache has invalid structure")
            return None
        return _validate_cache(parsed if isinstance(parsed, dict) else {})

    return await asyncio.to_thread(_read)


async def _save_install_counts_cache(cache: InstallCountsCache) -> None:
    path = _cache_path()
    temp_path = f"{path}.{secrets.token_hex(8)}.tmp"
    payload = {
        "version": cache.version,
        "fetchedAt": cache.fetched_at,
        "counts": cache.counts,
    }

    def _write() -> None:
        ensure_plugins_root_exists()
        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(json_stringify(payload, indent=2))
        with contextlib.suppress(OSError):
            os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
        log_for_debugging("Install counts cache saved successfully")

    try:
        await asyncio.to_thread(_write)
    except OSError as exc:
        log_error(exc)
        with contextlib.suppress(OSError):
            await asyncio.to_thread(os.unlink, temp_path)


async def _fetch_install_counts_from_github() -> list[dict[str, Any]]:
    log_for_debugging(f"Fetching install counts from {INSTALL_COUNTS_URL}")
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(INSTALL_COUNTS_URL)
            response.raise_for_status()
            data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("plugins"), list):
            raise ValueError("Invalid response format from install counts API")
        log_plugin_fetch(
            "install_counts",
            INSTALL_COUNTS_URL,
            "success",
            (time.perf_counter() - started) * 1000,
        )
        return data["plugins"]
    except Exception as exc:
        log_plugin_fetch(
            "install_counts",
            INSTALL_COUNTS_URL,
            "failure",
            (time.perf_counter() - started) * 1000,
            classify_fetch_error(exc),
        )
        raise


async def get_install_counts() -> dict[str, int] | None:
    """Return plugin id -> unique install count, or None if unavailable."""
    cache = await _load_install_counts_cache()
    if cache:
        log_for_debugging("Using cached install counts")
        log_plugin_fetch("install_counts", INSTALL_COUNTS_URL, "cache_hit", 0.0)
        return {str(e["plugin"]): int(e["unique_installs"]) for e in cache.counts if isinstance(e, dict)}

    try:
        counts = await _fetch_install_counts_from_github()
        new_cache = InstallCountsCache(
            version=INSTALL_COUNTS_CACHE_VERSION,
            fetched_at=time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            counts=counts,
        )
        await _save_install_counts_cache(new_cache)
        return {str(e["plugin"]): int(e["unique_installs"]) for e in counts if isinstance(e, dict)}
    except Exception as exc:
        log_error(exc if isinstance(exc, BaseException) else Exception(str(exc)))
        log_for_debugging(f"Failed to fetch install counts: {error_message(exc)}")
        return None


def format_install_count(count: int) -> str:
    if count < 1000:
        return str(count)
    if count < 1_000_000:
        k = count / 1000
        formatted = f"{k:.1f}"
        return f"{formatted[:-2]}K" if formatted.endswith(".0") else f"{formatted}K"
    m = count / 1_000_000
    formatted = f"{m:.1f}"
    return f"{formatted[:-2]}M" if formatted.endswith(".0") else f"{formatted}M"


__all__ = [
    "INSTALL_COUNTS_URL",
    "format_install_count",
    "get_install_counts",
]
