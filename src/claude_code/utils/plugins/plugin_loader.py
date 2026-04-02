"""
Discover and load Claude Code plugins (marketplace, session, builtin).

Migrated from: utils/plugins/pluginLoader.ts (structural port; marketplace load is stubbed).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

from ...bootstrap.state import get_inline_plugins
from ...types.plugin import (
    GenericPluginError,
    LoadedPlugin,
    PluginAuthor,
    PluginLoadResult,
    PluginManifest,
)
from ..debug import log_for_debugging
from ..env_utils import is_env_truthy
from .dependency_resolver import verify_and_demote
from .identifier import parse_plugin_identifier
from .managed_plugins import get_managed_plugin_names
from .marketplace_manager import load_plugins_from_marketplaces
from .plugin_directories import get_plugins_directory

_load_all_plugins_result: PluginLoadResult | None = None
_load_all_plugins_lock = asyncio.Lock()
_load_cache_only_result: PluginLoadResult | None = None
_load_cache_only_lock = asyncio.Lock()


def get_plugin_cache_path() -> str:
    return os.path.join(get_plugins_directory(), "cache")


def get_versioned_cache_path_in(base_dir: str, plugin_id: str, version: str) -> str:
    parsed = parse_plugin_identifier(plugin_id)
    plugin_name = parsed.name or plugin_id
    marketplace_raw = parsed.marketplace or "unknown"
    sanitized_marketplace = re.sub(r"[^a-zA-Z0-9\-_]", "-", marketplace_raw)
    sanitized_plugin = re.sub(r"[^a-zA-Z0-9\-_]", "-", plugin_name)
    sanitized_version = re.sub(r"[^a-zA-Z0-9\-_.]", "-", version)
    return os.path.join(
        base_dir,
        "cache",
        sanitized_marketplace,
        sanitized_plugin,
        sanitized_version,
    )


def get_versioned_cache_path(plugin_id: str, version: str) -> str:
    return get_versioned_cache_path_in(get_plugins_directory(), plugin_id, version)


def get_versioned_zip_cache_path(plugin_id: str, version: str) -> str:
    return f"{get_versioned_cache_path(plugin_id, version)}.zip"


def merge_plugin_sources(
    *,
    session: list[LoadedPlugin],
    marketplace: list[LoadedPlugin],
    builtin: list[LoadedPlugin],
    managed_names: set[str] | None,
) -> tuple[list[LoadedPlugin], list[Any]]:
    errors: list[Any] = []
    managed = managed_names or set()

    session_plugins: list[LoadedPlugin] = []
    for p in session:
        if p.name in managed:
            log_for_debugging(
                f'Plugin "{p.name}" from --plugin-dir is blocked by managed settings',
                level="warn",
            )
            errors.append(
                GenericPluginError(
                    type="generic-error",
                    source=p.source,
                    plugin=p.name,
                    error=(f'--plugin-dir copy of "{p.name}" ignored: plugin is locked by managed settings'),
                )
            )
            continue
        session_plugins.append(p)

    session_names = {p.name for p in session_plugins}
    marketplace_plugins = [p for p in marketplace if p.name not in session_names]

    merged = [*session_plugins, *marketplace_plugins, *builtin]
    return merged, errors


def _read_json_file(path: str) -> Any | None:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def _hooks_config(plugin_root: str) -> dict[str, Any] | None:
    for candidate in (
        os.path.join(plugin_root, "hooks", "hooks.json"),
        os.path.join(plugin_root, "hooks.json"),
    ):
        data = _read_json_file(candidate)
        if isinstance(data, dict):
            return data
    return None


async def _load_plugin_from_path(path: str, *, source: str) -> LoadedPlugin | None:
    def _build() -> LoadedPlugin | None:
        manifest_path = os.path.join(path, "plugin.json")
        raw = _read_json_file(manifest_path)
        if not isinstance(raw, dict):
            return None
        name = str(raw.get("name") or os.path.basename(path.rstrip(os.sep)))
        version = str(raw.get("version") or "0.0.0")
        author_raw = raw.get("author")
        author: PluginAuthor | None
        if isinstance(author_raw, str):
            author = PluginAuthor(name=author_raw)
        elif isinstance(author_raw, dict):
            author = PluginAuthor(
                name=str(author_raw.get("name") or ""),
                email=author_raw.get("email"),
                url=author_raw.get("url"),
            )
        else:
            author = None
        manifest = PluginManifest(
            name=name,
            version=version,
            description=raw.get("description"),
            author=author,
            homepage=raw.get("homepage"),
            repository=raw.get("repository"),
            license=raw.get("license"),
            keywords=raw.get("keywords"),
            dependencies=raw.get("dependencies"),
            user_config=raw.get("userConfig") if isinstance(raw.get("userConfig"), dict) else None,
        )
        commands_path = os.path.join(path, "commands")
        agents_path = os.path.join(path, "agents")
        skills_path = os.path.join(path, "skills")
        output_styles_path = os.path.join(path, "output-styles")
        return LoadedPlugin(
            name=name,
            manifest=manifest,
            path=os.path.abspath(path),
            source=source,
            repository=source,
            enabled=True,
            commands_path=commands_path if os.path.isdir(commands_path) else None,
            agents_path=agents_path if os.path.isdir(agents_path) else None,
            skills_path=skills_path if os.path.isdir(skills_path) else None,
            output_styles_path=output_styles_path if os.path.isdir(output_styles_path) else None,
            hooks_config=_hooks_config(path),
        )

    return await asyncio.to_thread(_build)


async def load_session_only_plugins(paths: list[str]) -> tuple[list[LoadedPlugin], list[Any]]:
    plugins: list[LoadedPlugin] = []
    errors: list[Any] = []
    for raw_path in paths:
        source = f"inline:{raw_path}"
        loaded = await _load_plugin_from_path(raw_path, source=source)
        if loaded:
            plugins.append(loaded)
        else:
            errors.append(
                GenericPluginError(
                    type="generic-error",
                    source=source,
                    error=f"Not a valid plugin directory: {raw_path}",
                )
            )
    return plugins, errors


def _builtin_plugins() -> tuple[list[LoadedPlugin], list[LoadedPlugin]]:
    return [], []


async def _assemble_plugin_load_result(*, cache_only: bool) -> PluginLoadResult:
    inline = get_inline_plugins()
    marketplace_coro = load_plugins_from_marketplaces(cache_only=cache_only)

    async def _empty_session() -> tuple[list[LoadedPlugin], list[Any]]:
        return [], []

    session_coro = load_session_only_plugins(inline) if inline else _empty_session()
    marketplace_result, session_result = await asyncio.gather(
        marketplace_coro,
        session_coro,
    )
    session_plugins, session_errors = session_result

    marketplace_plugins, marketplace_errors = marketplace_result
    builtin_enabled, builtin_disabled = _builtin_plugins()

    merged, merge_errors = merge_plugin_sources(
        session=session_plugins,
        marketplace=marketplace_plugins,
        builtin=[*builtin_enabled, *builtin_disabled],
        managed_names=get_managed_plugin_names(),
    )
    all_errors = [
        *marketplace_errors,
        *session_errors,
        *merge_errors,
    ]
    demoted, dep_errors = await verify_and_demote(merged)
    for p in merged:
        if p.source in demoted:
            p.enabled = False
    all_errors.extend(dep_errors)

    enabled_plugins = [p for p in merged if p.enabled]
    log_for_debugging(
        f"Found {len(merged)} plugins ({len(enabled_plugins)} enabled, {len(merged) - len(enabled_plugins)} disabled)",
    )
    cache_plugin_settings(enabled_plugins)
    return PluginLoadResult(
        enabled=enabled_plugins,
        disabled=[p for p in merged if not p.enabled],
        errors=all_errors,
    )


def cache_plugin_settings(plugins: list[LoadedPlugin]) -> None:
    """Hook for synchronous settings cache (TS parity)."""
    del plugins


async def load_all_plugins() -> PluginLoadResult:
    global _load_all_plugins_result
    async with _load_all_plugins_lock:
        if _load_all_plugins_result is not None:
            return _load_all_plugins_result
        result = await _assemble_plugin_load_result(cache_only=False)
        _load_all_plugins_result = result
        global _load_cache_only_result
        _load_cache_only_result = result
        return result


async def load_all_plugins_cache_only() -> PluginLoadResult:
    global _load_cache_only_result
    if is_env_truthy(os.environ.get("CLAUDE_CODE_SYNC_PLUGIN_INSTALL")):
        return await load_all_plugins()
    async with _load_cache_only_lock:
        if _load_cache_only_result is not None:
            return _load_cache_only_result
        result = await _assemble_plugin_load_result(cache_only=True)
        _load_cache_only_result = result
        return result


def clear_plugin_cache(reason: str | None = None) -> None:
    global _load_all_plugins_result, _load_cache_only_result
    if reason:
        log_for_debugging(f"clear_plugin_cache: invalidating caches ({reason})")
    _load_all_plugins_result = None
    _load_cache_only_result = None


__all__ = [
    "cache_plugin_settings",
    "clear_plugin_cache",
    "get_plugin_cache_path",
    "get_versioned_cache_path",
    "get_versioned_cache_path_in",
    "get_versioned_zip_cache_path",
    "load_all_plugins",
    "load_all_plugins_cache_only",
    "merge_plugin_sources",
]
