"""
Flagged plugin tracking (~/.claude/plugins/flagged-plugins.json).

Migrated from: utils/plugins/pluginFlagging.ts
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import secrets
import time
from datetime import UTC, datetime
from typing import Any

from ..debug import log_for_debugging
from ..log import log_error
from ..slow_operations import json_stringify
from .plugin_directories import ensure_plugins_root_exists, get_plugins_directory

FLAGGED_PLUGINS_FILENAME = "flagged-plugins.json"
SEEN_EXPIRY_MS = 48 * 60 * 60 * 1000

_cache: dict[str, dict[str, Any]] | None = None


def _flagged_path() -> str:
    return os.path.join(get_plugins_directory(), FLAGGED_PLUGINS_FILENAME)


def _parse_plugins_payload(content: str) -> dict[str, dict[str, Any]]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    plugins = parsed.get("plugins")
    if not isinstance(plugins, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for pid, entry in plugins.items():
        if not isinstance(entry, dict):
            continue
        flagged_at = entry.get("flaggedAt")
        if not isinstance(flagged_at, str):
            continue
        row: dict[str, Any] = {"flaggedAt": flagged_at}
        seen = entry.get("seenAt")
        if isinstance(seen, str):
            row["seenAt"] = seen
        out[str(pid)] = row
    return out


async def _read_from_disk() -> dict[str, dict[str, Any]]:

    def _read() -> dict[str, dict[str, Any]]:
        try:
            with open(_flagged_path(), encoding="utf-8") as handle:
                return _parse_plugins_payload(handle.read())
        except OSError:
            return {}

    return await asyncio.to_thread(_read)


async def _write_to_disk(plugins: dict[str, dict[str, Any]]) -> None:
    path = _flagged_path()
    temp_path = f"{path}.{secrets.token_hex(8)}.tmp"
    content = json_stringify({"plugins": plugins}, indent=2)

    def _write() -> None:
        ensure_plugins_root_exists()
        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        with contextlib.suppress(OSError):
            os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)

    try:
        await asyncio.to_thread(_write)
    except OSError as exc:
        log_error(exc)
        with contextlib.suppress(OSError):
            await asyncio.to_thread(os.unlink, temp_path)


async def load_flagged_plugins() -> None:
    global _cache
    all_plugins = await _read_from_disk()
    now_ms = int(time.time() * 1000)
    changed = False
    for pid, entry in list(all_plugins.items()):
        seen_at = entry.get("seenAt")
        if isinstance(seen_at, str):
            try:
                seen_ms = int(datetime.fromisoformat(seen_at.replace("Z", "+00:00")).timestamp() * 1000)
            except ValueError:
                continue
            if now_ms - seen_ms >= SEEN_EXPIRY_MS:
                del all_plugins[pid]
                changed = True
    _cache = all_plugins
    if changed:
        await _write_to_disk(all_plugins)


def get_flagged_plugins() -> dict[str, dict[str, Any]]:
    return dict(_cache or {})


async def add_flagged_plugin(plugin_id: str) -> None:
    global _cache
    if _cache is None:
        _cache = await _read_from_disk()
    updated = {
        **_cache,
        plugin_id: {"flaggedAt": datetime.now(UTC).replace(microsecond=0).isoformat()},
    }
    await _write_to_disk(updated)
    _cache = updated
    log_for_debugging(f"Flagged plugin: {plugin_id}")


async def remove_flagged_plugin(plugin_id: str) -> None:
    global _cache
    if _cache is None:
        _cache = await _read_from_disk()
    if plugin_id not in _cache:
        return
    rest = {k: v for k, v in _cache.items() if k != plugin_id}
    _cache = rest
    await _write_to_disk(rest)


__all__ = [
    "add_flagged_plugin",
    "get_flagged_plugins",
    "load_flagged_plugins",
    "remove_flagged_plugin",
]
