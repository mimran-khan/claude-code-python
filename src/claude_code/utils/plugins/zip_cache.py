"""
Plugin ZIP cache (mounted volume + session-local extraction).

Migrated from: utils/plugins/zipCache.ts
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import re
import secrets
import shutil
import tempfile
import zipfile
from typing import Any, Protocol, runtime_checkable

from ..debug import log_for_debugging
from ..env_utils import is_env_truthy


@runtime_checkable
class _MarketplaceSourceLike(Protocol):
    source: str


_session_plugin_cache_path: str | None = None
_session_plugin_cache_lock = asyncio.Lock()


def is_plugin_zip_cache_enabled() -> bool:
    return is_env_truthy(os.environ.get("CLAUDE_CODE_PLUGIN_USE_ZIP_CACHE"))


def get_plugin_zip_cache_path() -> str | None:
    if not is_plugin_zip_cache_enabled():
        return None
    raw = os.environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR")
    if not raw:
        return None
    from ..permissions.path_validation import expand_tilde

    return expand_tilde(raw)


def get_zip_cache_known_marketplaces_path() -> str:
    cache = get_plugin_zip_cache_path()
    if not cache:
        raise RuntimeError("Plugin zip cache is not enabled")
    return os.path.join(cache, "known_marketplaces.json")


def get_zip_cache_installed_plugins_path() -> str:
    cache = get_plugin_zip_cache_path()
    if not cache:
        raise RuntimeError("Plugin zip cache is not enabled")
    return os.path.join(cache, "installed_plugins.json")


def get_zip_cache_marketplaces_dir() -> str:
    cache = get_plugin_zip_cache_path()
    if not cache:
        raise RuntimeError("Plugin zip cache is not enabled")
    return os.path.join(cache, "marketplaces")


def get_zip_cache_plugins_dir() -> str:
    cache = get_plugin_zip_cache_path()
    if not cache:
        raise RuntimeError("Plugin zip cache is not enabled")
    return os.path.join(cache, "plugins")


def get_marketplace_json_relative_path(marketplace_name: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "-", marketplace_name)
    return os.path.join("marketplaces", f"{sanitized}.json")


def is_marketplace_source_supported_by_zip_cache(source: Any) -> bool:
    if isinstance(source, _MarketplaceSourceLike):
        return source.source in ("github", "git", "url", "settings")
    if isinstance(source, dict):
        return source.get("source") in ("github", "git", "url", "settings")
    return False


async def get_session_plugin_cache_path() -> str:
    global _session_plugin_cache_path
    async with _session_plugin_cache_lock:
        if _session_plugin_cache_path:
            return _session_plugin_cache_path
        suffix = secrets.token_hex(8)
        directory = os.path.join(tempfile.gettempdir(), f"claude-plugin-session-{suffix}")
        await asyncio.to_thread(os.makedirs, directory, exist_ok=False)
        _session_plugin_cache_path = directory
        log_for_debugging(f"Created session plugin cache at {directory}")
        return directory


async def cleanup_session_plugin_cache() -> None:
    global _session_plugin_cache_path
    path = _session_plugin_cache_path
    if not path:
        return
    try:
        await asyncio.to_thread(shutil.rmtree, path, ignore_errors=True)
        log_for_debugging(f"Cleaned up session plugin cache at {path}")
    except OSError as exc:
        log_for_debugging(f"Failed to clean up session plugin cache: {exc}")
    finally:
        _session_plugin_cache_path = None


def reset_session_plugin_cache() -> None:
    global _session_plugin_cache_path
    _session_plugin_cache_path = None


async def atomic_write_to_zip_cache(target_path: str, data: str | bytes) -> None:
    directory = os.path.dirname(target_path)
    await asyncio.to_thread(os.makedirs, directory, exist_ok=True)
    base = os.path.basename(target_path)
    tmp_name = f".{base}.tmp.{secrets.token_hex(4)}"
    tmp_path = os.path.join(directory, tmp_name)
    try:
        if isinstance(data, str):
            await asyncio.to_thread(_write_text, tmp_path, data)
        else:
            await asyncio.to_thread(_write_bytes, tmp_path, data)
        await asyncio.to_thread(os.replace, tmp_path, target_path)
    except Exception:
        with contextlib.suppress(OSError):
            await asyncio.to_thread(os.unlink, tmp_path)
        raise


def _write_text(path: str, data: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(data)


def _write_bytes(path: str, data: bytes) -> None:
    with open(path, "wb") as handle:
        handle.write(data)


async def create_zip_from_directory(source_dir: str) -> bytes:
    def _zip() -> bytes:
        import io

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(source_dir):
                if ".git" in root.split(os.sep):
                    continue
                for name in files:
                    full = os.path.join(root, name)
                    rel = os.path.relpath(full, source_dir)
                    try:
                        zf.write(full, arcname=rel.replace("\\", "/"))
                    except OSError as exc:
                        log_for_debugging(f"Failed to add file to zip {rel}: {exc}")
        return buffer.getvalue()

    data = await asyncio.to_thread(_zip)
    log_for_debugging(f"Created ZIP from {source_dir}: {len(data)} bytes")
    return data


async def extract_zip_to_directory(zip_path: str, target_dir: str) -> None:
    def _extract() -> None:
        os.makedirs(target_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                dest = zf.extract(member, path=target_dir)
                mode = member.external_attr >> 16
                if mode and mode & 0o111:
                    with contextlib.suppress(OSError):
                        os.chmod(dest, mode & 0o777)

    await asyncio.to_thread(_extract)
    log_for_debugging(f"Extracted ZIP {zip_path} to {target_dir}")


async def convert_directory_to_zip_in_place(dir_path: str, zip_path: str) -> None:
    zip_data = await create_zip_from_directory(dir_path)
    await atomic_write_to_zip_cache(zip_path, zip_data)
    await asyncio.to_thread(shutil.rmtree, dir_path, ignore_errors=True)


__all__ = [
    "atomic_write_to_zip_cache",
    "cleanup_session_plugin_cache",
    "convert_directory_to_zip_in_place",
    "create_zip_from_directory",
    "extract_zip_to_directory",
    "get_marketplace_json_relative_path",
    "get_plugin_zip_cache_path",
    "get_session_plugin_cache_path",
    "get_zip_cache_installed_plugins_path",
    "get_zip_cache_known_marketplaces_path",
    "get_zip_cache_marketplaces_dir",
    "get_zip_cache_plugins_dir",
    "is_marketplace_source_supported_by_zip_cache",
    "is_plugin_zip_cache_enabled",
    "reset_session_plugin_cache",
]
