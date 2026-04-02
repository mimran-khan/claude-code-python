"""
Plugin cache invalidation and orphaned version GC.

Migrated from: utils/plugins/cacheUtils.ts
"""

from __future__ import annotations

import asyncio
import os
import shutil
import time

from ..debug import log_for_debugging
from ..errors import get_errno_code
from ..log import log_error
from .installed_plugins_manager import load_installed_plugins_from_disk
from .load_plugin_agents import clear_plugin_agent_cache
from .load_plugin_commands import clear_plugin_command_cache
from .load_plugin_hooks import clear_plugin_hook_cache, prune_removed_plugin_hooks
from .load_plugin_output_styles import clear_plugin_output_style_cache
from .plugin_loader import clear_plugin_cache, get_plugin_cache_path
from .plugin_options_storage import clear_plugin_options_cache
from .zip_cache import is_plugin_zip_cache_enabled

ORPHANED_AT_FILENAME = ".orphaned_at"
_CLEANUP_AGE_MS = 7 * 24 * 60 * 60 * 1000


def clear_all_plugin_caches() -> None:
    clear_plugin_cache()
    clear_plugin_command_cache()
    clear_plugin_agent_cache()
    clear_plugin_hook_cache()

    async def _prune_safe() -> None:
        try:
            await prune_removed_plugin_hooks()
        except Exception as exc:
            log_error(exc)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        loop.create_task(_prune_safe())
    clear_plugin_options_cache()
    clear_plugin_output_style_cache()


def clear_all_caches() -> None:
    clear_all_plugin_caches()


async def mark_plugin_version_orphaned(version_path: str) -> None:
    marker = os.path.join(version_path, ORPHANED_AT_FILENAME)
    content = str(int(time.time() * 1000))

    def _write() -> None:
        os.makedirs(version_path, exist_ok=True)
        with open(marker, "w", encoding="utf-8") as handle:
            handle.write(content)

    try:
        await asyncio.to_thread(_write)
    except OSError as exc:
        log_for_debugging(f"Failed to write .orphaned_at: {version_path}: {exc}")


def _get_orphaned_at_path(version_path: str) -> str:
    return os.path.join(version_path, ORPHANED_AT_FILENAME)


async def _remove_orphaned_at_marker(version_path: str) -> None:
    path = _get_orphaned_at_path(version_path)
    try:
        await asyncio.to_thread(os.unlink, path)
    except OSError as exc:
        if get_errno_code(exc) == "ENOENT":
            return
        log_for_debugging(f"Failed to remove .orphaned_at: {version_path}: {exc}")


def _get_installed_version_paths() -> set[str] | None:
    try:
        disk = load_installed_plugins_from_disk()
        plugins = disk.get("plugins") or {}
        paths: set[str] = set()
        if not isinstance(plugins, dict):
            return paths
        for _scope, installations in plugins.items():
            if not isinstance(installations, list):
                continue
            for entry in installations:
                if isinstance(entry, dict):
                    p = entry.get("installPath") or entry.get("install_path")
                    if isinstance(p, str):
                        paths.add(p)
        return paths
    except Exception as exc:
        log_for_debugging(f"Failed to load installed plugins: {exc}")
        return None


async def _read_subdirs(dir_path: str) -> list[str]:
    def _read() -> list[str]:
        try:
            return [e for e in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, e))]
        except OSError:
            return []

    return await asyncio.to_thread(_read)


async def _remove_if_empty(dir_path: str) -> None:
    subs = await _read_subdirs(dir_path)
    if subs:
        return
    try:
        await asyncio.to_thread(shutil.rmtree, dir_path, ignore_errors=True)
    except OSError as exc:
        log_for_debugging(f"Failed to remove empty dir: {dir_path}: {exc}")


async def _process_orphaned_plugin_version(version_path: str, now_ms: float) -> None:
    orphaned_at_path = _get_orphaned_at_path(version_path)

    def _mtime() -> float | BaseException:
        try:
            return os.path.getmtime(orphaned_at_path) * 1000
        except OSError as exc:
            return exc

    mtime = await asyncio.to_thread(_mtime)
    if isinstance(mtime, BaseException):
        code = get_errno_code(mtime)
        if code == "ENOENT":
            await mark_plugin_version_orphaned(version_path)
            return
        log_for_debugging(f"Failed to stat orphaned marker: {version_path}: {mtime}")
        return

    if now_ms - mtime > _CLEANUP_AGE_MS:
        try:
            await asyncio.to_thread(shutil.rmtree, version_path, ignore_errors=True)
        except OSError as exc:
            log_for_debugging(f"Failed to delete orphaned version: {version_path}: {exc}")


async def cleanup_orphaned_plugin_versions_in_background() -> None:
    if is_plugin_zip_cache_enabled():
        return
    try:
        installed = _get_installed_version_paths()
        if not installed:
            return
        cache_path = get_plugin_cache_path()
        now = time.time() * 1000

        for p in installed:
            await _remove_orphaned_at_marker(p)

        for marketplace in await _read_subdirs(cache_path):
            mp = os.path.join(cache_path, marketplace)
            for plugin in await _read_subdirs(mp):
                pp = os.path.join(mp, plugin)
                for version in await _read_subdirs(pp):
                    vp = os.path.join(pp, version)
                    if vp in installed:
                        continue
                    await _process_orphaned_plugin_version(vp, now)
                await _remove_if_empty(pp)
            await _remove_if_empty(mp)
    except Exception as exc:
        log_for_debugging(f"Plugin cache cleanup failed: {exc}")


__all__ = [
    "ORPHANED_AT_FILENAME",
    "cleanup_orphaned_plugin_versions_in_background",
    "clear_all_caches",
    "clear_all_plugin_caches",
    "mark_plugin_version_orphaned",
]
