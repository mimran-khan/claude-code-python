"""
Installed plugin registry (``installed_plugins.json``).

Migrated from: utils/plugins/installedPluginsManager.ts
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Literal

from ...bootstrap.state import get_original_cwd
from ..cwd import get_cwd
from ..errors import error_message, is_enoent
from ..fs_operations import get_fs_implementation
from ..git_filesystem import get_head_for_dir
from ..log import log_error
from ..settings.constants import EditableSettingSource
from ..settings.settings import get_merged_settings, get_settings_for_source
from .identifier import parse_plugin_identifier, setting_source_to_scope
from .plugin_directories import get_plugin_cache_path, get_plugins_directory

logger = logging.getLogger(__name__)

PersistableScope = Literal["user", "project", "local", "managed"]

_migration_completed = False
_installed_plugins_cache_v2: dict[str, Any] | None = None
_in_memory_installed_plugins: dict[str, Any] | None = None


@dataclass
class InstalledPlugin:
    """V1-compatible return shape for remove_installed_plugin."""

    version: str
    installed_at: str
    install_path: str
    last_updated: str | None = None
    git_commit_sha: str | None = None


@dataclass
class PluginInstallationEntry:
    scope: PersistableScope
    install_path: str
    version: str | None = None
    installed_at: str | None = None
    last_updated: str | None = None
    git_commit_sha: str | None = None
    project_path: str | None = None


def _entry_from_dict(d: dict[str, Any]) -> PluginInstallationEntry:
    return PluginInstallationEntry(
        scope=d["scope"],
        install_path=d["installPath"],
        version=d.get("version"),
        installed_at=d.get("installedAt"),
        last_updated=d.get("lastUpdated"),
        git_commit_sha=d.get("gitCommitSha"),
        project_path=d.get("projectPath"),
    )


def _entry_to_dict(e: PluginInstallationEntry) -> dict[str, Any]:
    out: dict[str, Any] = {
        "scope": e.scope,
        "installPath": e.install_path,
        "version": e.version,
        "installedAt": e.installed_at,
        "lastUpdated": e.last_updated,
        "gitCommitSha": e.git_commit_sha,
    }
    if e.project_path is not None:
        out["projectPath"] = e.project_path
    return {k: v for k, v in out.items() if v is not None or k in ("scope", "installPath")}


def get_versioned_cache_path(plugin_id: str, version: str) -> str:
    parsed = parse_plugin_identifier(plugin_id)
    mkt = re.sub(r"[^a-zA-Z0-9\-_]", "-", parsed.marketplace or "unknown")
    plug = re.sub(r"[^a-zA-Z0-9\-_]", "-", parsed.name or plugin_id)
    ver = re.sub(r"[^a-zA-Z0-9\-_.]", "-", version)
    return os.path.join(get_plugins_directory(), "cache", mkt, plug, ver)


def get_installed_plugins_file_path() -> str:
    return os.path.join(get_plugins_directory(), "installed_plugins.json")


def get_installed_plugins_v2_file_path() -> str:
    return os.path.join(get_plugins_directory(), "installed_plugins_v2.json")


def clear_installed_plugins_cache() -> None:
    global _installed_plugins_cache_v2, _in_memory_installed_plugins
    _installed_plugins_cache_v2 = None
    _in_memory_installed_plugins = None
    logger.debug("Cleared installed plugins cache")


def reset_migration_state() -> None:
    global _migration_completed
    _migration_completed = False


def _read_json_file(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json_file(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def read_installed_plugins_file_raw() -> tuple[int, Any] | None:
    fs = get_fs_implementation()
    file_path = get_installed_plugins_file_path()
    try:
        content = fs.read_file_sync(file_path, encoding="utf-8")
    except OSError as e:
        if is_enoent(e):
            return None
        raise
    data = json.loads(content)
    version = data.get("version") if isinstance(data, dict) else None
    ver = int(version) if isinstance(version, int) else 1
    return ver, data


def migrate_v1_to_v2(v1_data: dict[str, Any]) -> dict[str, Any]:
    plugins_out: dict[str, list[dict[str, Any]]] = {}
    plugins = v1_data.get("plugins") or {}
    if not isinstance(plugins, dict):
        return {"version": 2, "plugins": {}}
    for plugin_id, plugin in plugins.items():
        if not isinstance(plugin, dict):
            continue
        version = str(plugin.get("version", "unknown"))
        plugins_out[plugin_id] = [
            {
                "scope": "user",
                "installPath": get_versioned_cache_path(plugin_id, version),
                "version": version,
                "installedAt": plugin.get("installedAt", ""),
                "lastUpdated": plugin.get("lastUpdated"),
                "gitCommitSha": plugin.get("gitCommitSha"),
            }
        ]
    return {"version": 2, "plugins": plugins_out}


def cleanup_legacy_cache(v2_data: dict[str, Any]) -> None:
    fs = get_fs_implementation()
    cache_path = get_plugin_cache_path()
    referenced: set[str] = set()
    plugins = v2_data.get("plugins") or {}
    if isinstance(plugins, dict):
        for installations in plugins.values():
            if not isinstance(installations, list):
                continue
            for entry in installations:
                if isinstance(entry, dict) and entry.get("installPath"):
                    referenced.add(entry["installPath"])
    try:
        for dirent in fs.readdir_sync(cache_path):
            if not dirent.is_dir(follow_symlinks=False):
                continue
            entry_path = os.path.join(cache_path, dirent.name)
            sub = fs.readdir_sync(entry_path)
            has_versioned = False
            for sd in sub:
                if not sd.is_dir(follow_symlinks=False):
                    continue
                sub_path = os.path.join(entry_path, sd.name)
                try:
                    vers = fs.readdir_sync(sub_path)
                except OSError:
                    continue
                if any(v.is_dir(follow_symlinks=False) for v in vers):
                    has_versioned = True
                    break
            if has_versioned:
                continue
            if entry_path not in referenced:
                fs.rm_sync(entry_path, recursive=True, force=True)
                logger.debug("Cleaned up legacy cache directory: %s", dirent.name)
    except OSError as e:
        logger.warning("Failed to clean up legacy cache: %s", error_message(e))


def migrate_to_single_plugin_file() -> None:
    global _migration_completed
    if _migration_completed:
        return
    fs = get_fs_implementation()
    main_file_path = get_installed_plugins_file_path()
    v2_file_path = get_installed_plugins_v2_file_path()
    try:
        try:
            fs.rename_sync(v2_file_path, main_file_path)
            logger.debug("Renamed installed_plugins_v2.json to installed_plugins.json")
            v2_data = load_installed_plugins_v2()
            cleanup_legacy_cache(v2_data)
            _migration_completed = True
            return
        except OSError as e:
            if not is_enoent(e):
                raise

        try:
            main_content = fs.read_file_sync(main_file_path, encoding="utf-8")
        except OSError as e:
            if is_enoent(e):
                _migration_completed = True
                return
            raise

        main_data = json.loads(main_content)
        version = main_data.get("version") if isinstance(main_data, dict) else 1
        ver = int(version) if isinstance(version, int) else 1
        if ver == 1:
            v2_data = migrate_v1_to_v2(main_data if isinstance(main_data, dict) else {})
            _write_json_file(main_file_path, v2_data)
            logger.debug("Converted installed_plugins.json from V1 to V2")
            cleanup_legacy_cache(v2_data)
        _migration_completed = True
    except Exception as e:
        logger.error("Failed to migrate plugin files: %s", error_message(e))
        log_error(e if isinstance(e, Exception) else Exception(str(e)))
        _migration_completed = True


def _normalize_v2(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("version") != 2:
        raise ValueError("expected version 2")
    plugins = data.get("plugins")
    if not isinstance(plugins, dict):
        raise ValueError("invalid plugins")
    return {"version": 2, "plugins": plugins}


def load_installed_plugins_v2() -> dict[str, Any]:
    global _installed_plugins_cache_v2
    if _installed_plugins_cache_v2 is not None:
        return _installed_plugins_cache_v2
    try:
        raw = read_installed_plugins_file_raw()
        if raw:
            ver, data = raw
            if ver == 2 and isinstance(data, dict):
                _installed_plugins_cache_v2 = _normalize_v2(data)
                return _installed_plugins_cache_v2
            if isinstance(data, dict):
                v1_plugins = data.get("plugins")
                if isinstance(v1_plugins, dict):
                    v2 = migrate_v1_to_v2(data)
                    _installed_plugins_cache_v2 = v2
                    logger.debug("Loaded and converted plugins from V1 format")
                    return _installed_plugins_cache_v2
        _installed_plugins_cache_v2 = {"version": 2, "plugins": {}}
        return _installed_plugins_cache_v2
    except Exception as e:
        logger.error("Failed to load installed_plugins.json: %s", error_message(e))
        log_error(e if isinstance(e, Exception) else Exception(str(e)))
        _installed_plugins_cache_v2 = {"version": 2, "plugins": {}}
        return _installed_plugins_cache_v2


def save_installed_plugins_v2(data: dict[str, Any]) -> None:
    global _installed_plugins_cache_v2
    file_path = get_installed_plugins_file_path()
    fs = get_fs_implementation()
    fs.mkdir_sync(get_plugins_directory(), mode=0o755)
    _write_json_file(file_path, data)
    _installed_plugins_cache_v2 = data


def load_installed_plugins_from_disk() -> dict[str, Any]:
    try:
        raw = read_installed_plugins_file_raw()
        if not raw:
            return {"version": 2, "plugins": {}}
        ver, data = raw
        if ver == 2 and isinstance(data, dict):
            return _normalize_v2(data)
        if isinstance(data, dict):
            return migrate_v1_to_v2(data)
        return {"version": 2, "plugins": {}}
    except Exception as e:
        logger.error("Failed to load installed plugins from disk: %s", error_message(e))
        return {"version": 2, "plugins": {}}


def add_plugin_installation(
    plugin_id: str,
    scope: PersistableScope,
    install_path: str,
    metadata: dict[str, Any],
    project_path: str | None = None,
) -> None:
    data = load_installed_plugins_from_disk()
    plugins: dict[str, list[dict[str, Any]]] = dict(data.get("plugins") or {})
    installations = list(plugins.get(plugin_id, []))
    idx = next(
        (i for i, e in enumerate(installations) if e.get("scope") == scope and e.get("projectPath") == project_path),
        -1,
    )
    from datetime import datetime

    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    new_entry: dict[str, Any] = {
        "scope": scope,
        "installPath": install_path,
        "version": metadata.get("version"),
        "installedAt": metadata.get("installedAt") or now,
        "lastUpdated": now,
        "gitCommitSha": metadata.get("gitCommitSha"),
    }
    if project_path:
        new_entry["projectPath"] = project_path
    if idx >= 0:
        installations[idx] = new_entry
    else:
        installations.append(new_entry)
    plugins[plugin_id] = installations
    data["plugins"] = plugins
    save_installed_plugins_v2(data)


def remove_plugin_installation(
    plugin_id: str,
    scope: PersistableScope,
    project_path: str | None = None,
) -> None:
    data = load_installed_plugins_from_disk()
    plugins: dict[str, list[dict[str, Any]]] = dict(data.get("plugins") or {})
    installations = plugins.get(plugin_id)
    if not installations:
        return
    plugins[plugin_id] = [
        e for e in installations if not (e.get("scope") == scope and e.get("projectPath") == project_path)
    ]
    if not plugins[plugin_id]:
        del plugins[plugin_id]
    data["plugins"] = plugins
    save_installed_plugins_v2(data)


def get_in_memory_installed_plugins() -> dict[str, Any]:
    global _in_memory_installed_plugins
    if _in_memory_installed_plugins is None:
        _in_memory_installed_plugins = load_installed_plugins_v2()
    return _in_memory_installed_plugins


def update_installation_path_on_disk(
    plugin_id: str,
    scope: PersistableScope,
    project_path: str | None,
    new_path: str,
    new_version: str,
    git_commit_sha: str | None = None,
) -> None:
    global _installed_plugins_cache_v2
    disk_data = load_installed_plugins_from_disk()
    installations = disk_data.get("plugins", {}).get(plugin_id)
    if not installations:
        logger.debug("Cannot update %s on disk: plugin not found", plugin_id)
        return
    for entry in installations:
        if entry.get("scope") == scope and entry.get("projectPath") == project_path:
            entry["installPath"] = new_path
            entry["version"] = new_version
            from datetime import datetime

            entry["lastUpdated"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            if git_commit_sha is not None:
                entry["gitCommitSha"] = git_commit_sha
            _write_json_file(get_installed_plugins_file_path(), disk_data)
            _installed_plugins_cache_v2 = None
            logger.debug("Updated %s on disk to version %s", plugin_id, new_version)
            return
    logger.debug("Cannot update %s on disk: no installation for scope %s", plugin_id, scope)


def has_pending_updates() -> bool:
    return get_pending_update_count() > 0


def get_pending_update_count() -> int:
    return len(get_pending_updates_details())


def get_pending_updates_details() -> list[dict[str, str]]:
    memory_state = get_in_memory_installed_plugins()
    disk_state = load_installed_plugins_from_disk()
    updates: list[dict[str, str]] = []
    d_plugins = disk_state.get("plugins") or {}
    m_plugins = memory_state.get("plugins") or {}
    if not isinstance(d_plugins, dict) or not isinstance(m_plugins, dict):
        return updates
    for plugin_id, disk_installations in d_plugins.items():
        memory_installations = m_plugins.get(plugin_id)
        if not memory_installations:
            continue
        if not isinstance(disk_installations, list) or not isinstance(memory_installations, list):
            continue
        for disk_entry in disk_installations:
            if not isinstance(disk_entry, dict):
                continue
            for mem_entry in memory_installations:
                if not isinstance(mem_entry, dict):
                    continue
                if (
                    mem_entry.get("scope") == disk_entry.get("scope")
                    and mem_entry.get("projectPath") == disk_entry.get("projectPath")
                    and mem_entry.get("installPath") != disk_entry.get("installPath")
                ):
                    updates.append(
                        {
                            "pluginId": plugin_id,
                            "scope": str(disk_entry.get("scope", "")),
                            "oldVersion": str(mem_entry.get("version") or "unknown"),
                            "newVersion": str(disk_entry.get("version") or "unknown"),
                        }
                    )
    return updates


def reset_in_memory_state() -> None:
    global _in_memory_installed_plugins
    _in_memory_installed_plugins = None


async def initialize_versioned_plugins() -> None:
    migrate_to_single_plugin_file()
    try:
        await migrate_from_enabled_plugins()
    except Exception as e:
        log_error(e if isinstance(e, Exception) else Exception(str(e)))
    data = get_in_memory_installed_plugins()
    n = len(data.get("plugins") or {})
    logger.debug("Initialized versioned plugins system with %s plugins", n)


def remove_all_plugins_for_marketplace(marketplace_name: str) -> dict[str, Any]:
    if not marketplace_name:
        return {"orphanedPaths": [], "removedPluginIds": []}
    data = load_installed_plugins_from_disk()
    suffix = f"@{marketplace_name}"
    orphaned: set[str] = set()
    removed: list[str] = []
    plugins = dict(data.get("plugins") or {})
    for plugin_id in list(plugins.keys()):
        if not plugin_id.endswith(suffix):
            continue
        for entry in plugins.get(plugin_id, []) or []:
            if isinstance(entry, dict) and entry.get("installPath"):
                orphaned.add(entry["installPath"])
        del plugins[plugin_id]
        removed.append(plugin_id)
    data["plugins"] = plugins
    if removed:
        save_installed_plugins_v2(data)
    return {"orphanedPaths": list(orphaned), "removedPluginIds": removed}


def is_installation_relevant_to_current_project(entry: PluginInstallationEntry) -> bool:
    return entry.scope in ("user", "managed") or entry.project_path == get_original_cwd()


def is_plugin_installed(plugin_id: str) -> bool:
    v2 = load_installed_plugins_v2()
    installations = v2.get("plugins", {}).get(plugin_id)
    if not installations:
        return False
    entries = [_entry_from_dict(e) for e in installations if isinstance(e, dict)]
    if not any(is_installation_relevant_to_current_project(e) for e in entries):
        return False
    merged = get_merged_settings()
    ep = merged.get("enabledPlugins")
    if not isinstance(ep, dict):
        return False
    return plugin_id in ep


def is_plugin_globally_installed(plugin_id: str) -> bool:
    v2 = load_installed_plugins_v2()
    installations = v2.get("plugins", {}).get(plugin_id)
    if not installations:
        return False
    entries = [_entry_from_dict(e) for e in installations if isinstance(e, dict)]
    if not any(e.scope in ("user", "managed") for e in entries):
        return False
    merged = get_merged_settings()
    ep = merged.get("enabledPlugins")
    if not isinstance(ep, dict):
        return False
    return plugin_id in ep


def add_installed_plugin(
    plugin_id: str,
    metadata: InstalledPlugin,
    scope: PersistableScope = "user",
    project_path: str | None = None,
) -> None:
    data = load_installed_plugins_from_disk()
    plugins: dict[str, list[dict[str, Any]]] = dict(data.get("plugins") or {})
    installations = list(plugins.get(plugin_id, []))
    v2_entry: dict[str, Any] = {
        "scope": scope,
        "installPath": metadata.install_path,
        "version": metadata.version,
        "installedAt": metadata.installed_at,
        "lastUpdated": metadata.last_updated,
        "gitCommitSha": metadata.git_commit_sha,
    }
    if project_path:
        v2_entry["projectPath"] = project_path
    idx = next(
        (i for i, e in enumerate(installations) if e.get("scope") == scope and e.get("projectPath") == project_path),
        -1,
    )
    is_update = idx >= 0
    if is_update:
        installations[idx] = v2_entry
    else:
        installations.append(v2_entry)
    plugins[plugin_id] = installations
    data["plugins"] = plugins
    save_installed_plugins_v2(data)
    logger.debug(
        "%s installed plugin: %s (scope: %s)",
        "Updated" if is_update else "Added",
        plugin_id,
        scope,
    )


def remove_installed_plugin(plugin_id: str) -> InstalledPlugin | None:
    data = load_installed_plugins_from_disk()
    plugins: dict[str, list[dict[str, Any]]] = dict(data.get("plugins") or {})
    installations = plugins.get(plugin_id)
    if not installations:
        return None
    first = installations[0]
    meta = InstalledPlugin(
        version=str(first.get("version") or "unknown"),
        installed_at=str(first.get("installedAt") or ""),
        last_updated=first.get("lastUpdated"),
        install_path=str(first.get("installPath") or ""),
        git_commit_sha=first.get("gitCommitSha"),
    )
    del plugins[plugin_id]
    data["plugins"] = plugins
    save_installed_plugins_v2(data)
    logger.debug("Removed installed plugin: %s", plugin_id)
    return meta


def delete_plugin_cache(install_path: str) -> None:
    fs = get_fs_implementation()
    try:
        fs.rm_sync(install_path, recursive=True, force=True)
        logger.debug("Deleted plugin cache at %s", install_path)
        cache_path = get_plugin_cache_path()
        if "/cache/" in install_path.replace("\\", "/") and install_path.startswith(cache_path):
            plugin_dir = os.path.dirname(install_path)
            if plugin_dir != cache_path and plugin_dir.startswith(cache_path):
                try:
                    if fs.is_dir_empty_sync(plugin_dir):
                        fs.rmdir_sync(plugin_dir)
                        logger.debug("Deleted empty plugin directory at %s", plugin_dir)
                except OSError:
                    pass
    except OSError as e:
        log_error(e)
        raise RuntimeError(
            f"Failed to delete plugin cache at {install_path}: {error_message(e)}",
        ) from e


async def get_git_commit_sha(dir_path: str) -> str | None:
    return await get_head_for_dir(dir_path)


def _plugin_version_from_manifest(plugin_cache_path: str, plugin_id: str) -> str:
    fs = get_fs_implementation()
    manifest_path = os.path.join(plugin_cache_path, ".claude-plugin", "plugin.json")
    try:
        raw = fs.read_file_sync(manifest_path, encoding="utf-8")
        manifest = json.loads(raw)
        return str(manifest.get("version") or "unknown")
    except OSError:
        logger.debug("Could not read version from manifest for %s", plugin_id)
        return "unknown"


async def migrate_from_enabled_plugins() -> None:
    settings = get_merged_settings()
    enabled_plugins = settings.get("enabledPlugins") or {}
    if not isinstance(enabled_plugins, dict) or not enabled_plugins:
        return

    raw = read_installed_plugins_file_raw()
    file_exists = raw is not None
    is_v2 = file_exists and raw is not None and raw[0] == 2

    if is_v2 and raw:
        _, pdata = raw
        if isinstance(pdata, dict):
            plugins = pdata.get("plugins")
            if isinstance(plugins, dict):
                all_exist = all(
                    plugins.get(pid) and len(plugins[pid]) > 0
                    for pid in enabled_plugins
                    if isinstance(pid, str) and "@" in pid
                )
                if all_exist:
                    logger.debug("All plugins already exist, skipping migration")
                    return

    from datetime import datetime

    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    project_path_cwd = get_cwd()

    plugin_scope_from_settings: dict[str, dict[str, Any]] = {}
    sources: tuple[EditableSettingSource, ...] = (
        "userSettings",
        "projectSettings",
        "localSettings",
    )
    for source in sources:
        src = get_settings_for_source(source) or {}
        src_ep = src.get("enabledPlugins") or {}
        if not isinstance(src_ep, dict):
            continue
        for plugin_id in src_ep:
            if "@" not in plugin_id:
                continue
            scope = setting_source_to_scope(source)
            plugin_scope_from_settings[plugin_id] = {
                "scope": scope,
                "projectPath": None if scope == "user" else project_path_cwd,
            }

    v2_plugins: dict[str, list[dict[str, Any]]] = {}
    if file_exists:
        existing = load_installed_plugins_v2()
        v2_plugins = {k: list(v) for k, v in (existing.get("plugins") or {}).items()}

    updated_count = 0
    added_count = 0

    try:
        from .marketplace_manager import get_plugin_by_id as _fetch_plugin_by_id
    except (ImportError, AttributeError):
        _fetch_plugin_by_id = None

    for plugin_id, scope_info in plugin_scope_from_settings.items():
        existing_installations = v2_plugins.get(plugin_id)
        if existing_installations and len(existing_installations) > 0:
            ex = existing_installations[0]
            if ex.get("scope") != scope_info["scope"] or ex.get("projectPath") != scope_info.get("projectPath"):
                ex["scope"] = scope_info["scope"]
                if scope_info.get("projectPath"):
                    ex["projectPath"] = scope_info["projectPath"]
                elif "projectPath" in ex:
                    del ex["projectPath"]
                ex["lastUpdated"] = now
                updated_count += 1
            continue

        parsed = parse_plugin_identifier(plugin_id)
        if not parsed.name or not parsed.marketplace:
            continue
        try:
            if _fetch_plugin_by_id is None:
                continue
            plugin_info = await _fetch_plugin_by_id(plugin_id)
            if not plugin_info:
                logger.debug("Plugin %s not found in marketplace, skipping", plugin_id)
                continue
            entry = plugin_info.get("entry")
            marketplace_install_location = plugin_info.get(
                "marketplaceInstallLocation",
                plugin_info.get("marketplace_install_location", ""),
            )
            if entry is None:
                continue
            install_path = ""
            version = "unknown"
            git_sha: str | None = None
            src = entry.get("source")
            if isinstance(src, str):
                install_path = os.path.join(marketplace_install_location, src)
                version = _plugin_version_from_manifest(install_path, plugin_id)
                git_sha = await get_git_commit_sha(install_path)
            else:
                cache_path = get_plugin_cache_path()
                sanitized = re.sub(r"[^a-zA-Z0-9-_]", "-", parsed.name)
                plugin_cache_path = os.path.join(cache_path, sanitized)
                fs = get_fs_implementation()
                try:
                    sub = await fs.readdir(plugin_cache_path)
                    dir_entries = [x.name for x in sub]
                except OSError as e:
                    if is_enoent(e):
                        logger.debug("External plugin %s not in cache, skipping", plugin_id)
                        continue
                    raise
                install_path = plugin_cache_path
                if ".claude-plugin" in dir_entries:
                    version = _plugin_version_from_manifest(plugin_cache_path, plugin_id)
                git_sha = await get_git_commit_sha(plugin_cache_path)
            if version == "unknown" and entry.get("version"):
                version = str(entry["version"])
            if version == "unknown" and git_sha:
                version = git_sha[:12]
            scope = scope_info["scope"]
            proj = scope_info.get("projectPath")
            row: dict[str, Any] = {
                "scope": scope,
                "installPath": get_versioned_cache_path(plugin_id, version),
                "version": version,
                "installedAt": now,
                "lastUpdated": now,
                "gitCommitSha": git_sha,
            }
            if proj:
                row["projectPath"] = proj
            v2_plugins[plugin_id] = [row]
            added_count += 1
        except Exception as e:
            logger.debug("Failed to add plugin %s: %s", plugin_id, e)

    if not file_exists or updated_count > 0 or added_count > 0:
        save_installed_plugins_v2({"version": 2, "plugins": v2_plugins})
        logger.debug(
            "Sync completed: %s added, %s updated in installed_plugins.json",
            added_count,
            updated_count,
        )


__all__ = [
    "InstalledPlugin",
    "PersistableScope",
    "PluginInstallationEntry",
    "add_installed_plugin",
    "add_plugin_installation",
    "clear_installed_plugins_cache",
    "delete_plugin_cache",
    "get_git_commit_sha",
    "get_in_memory_installed_plugins",
    "get_installed_plugins_file_path",
    "get_installed_plugins_v2_file_path",
    "get_pending_update_count",
    "get_pending_updates_details",
    "get_versioned_cache_path",
    "has_pending_updates",
    "initialize_versioned_plugins",
    "is_installation_relevant_to_current_project",
    "is_plugin_globally_installed",
    "is_plugin_installed",
    "load_installed_plugins_from_disk",
    "load_installed_plugins_v2",
    "migrate_from_enabled_plugins",
    "migrate_to_single_plugin_file",
    "remove_all_plugins_for_marketplace",
    "remove_installed_plugin",
    "remove_plugin_installation",
    "reset_in_memory_state",
    "reset_migration_state",
    "update_installation_path_on_disk",
]
