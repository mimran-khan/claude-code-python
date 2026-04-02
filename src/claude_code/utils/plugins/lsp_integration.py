"""
Load and resolve LSP server definitions from plugins.

Migrated from: utils/plugins/lspPluginIntegration.ts
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ...services.mcp.env_expansion import expand_env_vars_in_string
from ...types.plugin import LoadedPlugin, LspConfigInvalidError, PluginError
from ..errors import is_enoent
from ..log import log_error
from .plugin_directories import get_plugin_data_dir

logger = logging.getLogger(__name__)


class LspServerConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    workspace_folder: str | None = Field(None, alias="workspaceFolder")

    def to_runtime_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.command is not None:
            d["command"] = self.command
        if self.args is not None:
            d["args"] = self.args
        if self.env is not None:
            d["env"] = dict(self.env)
        if self.workspace_folder is not None:
            d["workspaceFolder"] = self.workspace_folder
        return d


def _substitute_plugin_variables(value: str, plugin: LoadedPlugin) -> str:
    return value.replace("${CLAUDE_PLUGIN_ROOT}", plugin.path).replace(
        "${PLUGIN_ROOT}",
        plugin.path,
    )


def _substitute_user_config_variables(value: str, user_config: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        return user_config.get(key, m.group(0))

    return re.sub(r"\$\{user_config\.([^}]+)\}", repl, value)


def get_plugin_storage_id(plugin_source: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\-_]", "-", plugin_source)


def load_plugin_options(_storage_id: str) -> dict[str, str]:
    """Stub: persisted plugin user options (keychain in TS). Returns empty until wired."""
    return {}


def validate_path_within_plugin(plugin_path: str, relative_path: str) -> str | None:
    resolved_plugin = os.path.realpath(plugin_path)
    resolved_file = os.path.realpath(os.path.join(plugin_path, relative_path))
    rel = os.path.relpath(resolved_file, resolved_plugin)
    if rel.startswith("..") or os.path.isabs(rel):
        return None
    return resolved_file


async def load_plugin_lsp_servers(
    plugin: LoadedPlugin,
    errors: list[PluginError] | None = None,
) -> dict[str, dict[str, Any]] | None:
    errs = errors if errors is not None else []
    servers: dict[str, dict[str, Any]] = {}

    lsp_json_path = os.path.join(plugin.path, ".lsp.json")
    try:
        with open(lsp_json_path, encoding="utf-8") as f:
            parsed = json.load(f)
        if not isinstance(parsed, dict):
            raise ValueError("root must be object")
        for name, cfg in parsed.items():
            if not isinstance(name, str):
                continue
            try:
                model = LspServerConfigModel.model_validate(cfg)
                servers[name] = model.to_runtime_dict()
            except Exception as e:
                msg = f"LSP config validation failed for .lsp.json in plugin {plugin.name}: {e}"
                log_error(RuntimeError(msg))
                errs.append(
                    LspConfigInvalidError(
                        plugin=plugin.name,
                        server_name=".lsp.json",
                        validation_error=str(e),
                    )
                )
    except OSError as e:
        if not is_enoent(e):
            log_error(e)
            errs.append(
                LspConfigInvalidError(
                    plugin=plugin.name,
                    server_name=".lsp.json",
                    validation_error=str(e),
                )
            )
    except json.JSONDecodeError as e:
        log_error(e)
        errs.append(
            LspConfigInvalidError(
                plugin=plugin.name,
                server_name=".lsp.json",
                validation_error=f"Invalid JSON: {e}",
            )
        )

    raw_lsp = plugin.manifest.lsp_servers
    if raw_lsp is not None:
        extra = await _load_lsp_servers_from_manifest(
            raw_lsp,
            plugin.path,
            plugin.name,
            errs,
        )
        if extra:
            servers.update(extra)

    return servers if servers else None


async def _load_lsp_servers_from_manifest(
    declaration: Any,
    plugin_path: str,
    plugin_name: str,
    errors: list[PluginError],
) -> dict[str, dict[str, Any]] | None:
    servers: dict[str, dict[str, Any]] = {}
    decls = declaration if isinstance(declaration, list) else [declaration]
    for decl in decls:
        if isinstance(decl, str):
            validated = validate_path_within_plugin(plugin_path, decl)
            if not validated:
                msg = f"Security: Path traversal blocked in plugin {plugin_name}: {decl}"
                log_error(RuntimeError(msg))
                errors.append(
                    LspConfigInvalidError(
                        plugin=plugin_name,
                        server_name=decl,
                        validation_error="Invalid path: must be relative and within plugin directory",
                    )
                )
                continue
            try:
                with open(validated, encoding="utf-8") as f:
                    parsed = json.load(f)
                if not isinstance(parsed, dict):
                    raise ValueError("root must be object")
                for name, cfg in parsed.items():
                    if not isinstance(name, str):
                        continue
                    model = LspServerConfigModel.model_validate(cfg)
                    servers[name] = model.to_runtime_dict()
            except Exception as e:
                log_error(e if isinstance(e, Exception) else Exception(str(e)))
                errors.append(
                    LspConfigInvalidError(
                        plugin=plugin_name,
                        server_name=decl,
                        validation_error=str(e),
                    )
                )
        elif isinstance(decl, dict):
            for server_name, config in decl.items():
                try:
                    model = LspServerConfigModel.model_validate(config)
                    servers[server_name] = model.to_runtime_dict()
                except Exception as e:
                    msg = f"LSP validation failed for inline server {server_name!r} in plugin {plugin_name}: {e}"
                    log_error(RuntimeError(msg))
                    errors.append(
                        LspConfigInvalidError(
                            plugin=plugin_name,
                            server_name=server_name,
                            validation_error=str(e),
                        )
                    )
    return servers if servers else None


def resolve_plugin_lsp_environment(
    config: dict[str, Any],
    plugin: LoadedPlugin,
    user_config: dict[str, str] | None = None,
) -> dict[str, Any]:
    missing: list[str] = []

    def resolve_value(value: str) -> str:
        nonlocal missing
        s = _substitute_plugin_variables(value, plugin)
        if user_config:
            s = _substitute_user_config_variables(s, user_config)
        result = expand_env_vars_in_string(s)
        missing.extend(result.missing_vars)
        return result.expanded

    resolved = dict(config)
    if resolved.get("command"):
        resolved["command"] = resolve_value(str(resolved["command"]))
    if resolved.get("args"):
        resolved["args"] = [resolve_value(str(a)) for a in resolved["args"]]
    env_out: dict[str, str] = {
        "CLAUDE_PLUGIN_ROOT": plugin.path,
        "CLAUDE_PLUGIN_DATA": get_plugin_data_dir(plugin.source),
        **(resolved.get("env") or {}),
    }
    for key, val in list(env_out.items()):
        if key in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA"):
            continue
        env_out[key] = resolve_value(str(val))
    resolved["env"] = env_out
    if resolved.get("workspaceFolder"):
        resolved["workspaceFolder"] = resolve_value(str(resolved["workspaceFolder"]))
    if missing:
        u = ", ".join(sorted(set(missing)))
        log_error(RuntimeError(f"Missing environment variables in plugin LSP config: {u}"))
        logger.warning("Missing environment variables in plugin LSP config: %s", u)
    return resolved


def add_plugin_scope_to_lsp_servers(
    servers: dict[str, dict[str, Any]],
    plugin_name: str,
) -> dict[str, dict[str, Any]]:
    scoped: dict[str, dict[str, Any]] = {}
    for name, cfg in servers.items():
        scoped_name = f"plugin:{plugin_name}:{name}"
        scoped[scoped_name] = {
            **cfg,
            "scope": "dynamic",
            "source": plugin_name,
        }
    return scoped


async def get_plugin_lsp_servers(
    plugin: LoadedPlugin,
    errors: list[PluginError] | None = None,
) -> dict[str, dict[str, Any]] | None:
    if not plugin.enabled:
        return None
    errs = errors if errors is not None else []
    servers = plugin.lsp_servers or await load_plugin_lsp_servers(plugin, errs)
    if not servers:
        return None
    user_cfg = None
    if plugin.manifest.user_config:
        user_cfg = load_plugin_options(get_plugin_storage_id(plugin.source))
    resolved: dict[str, dict[str, Any]] = {}
    for name, cfg in servers.items():
        resolved[name] = resolve_plugin_lsp_environment(cfg, plugin, user_cfg)
    return add_plugin_scope_to_lsp_servers(resolved, plugin.name)


async def extract_lsp_servers_from_plugins(
    plugins: list[LoadedPlugin],
    errors: list[PluginError] | None = None,
) -> dict[str, dict[str, Any]]:
    errs = errors if errors is not None else []
    all_servers: dict[str, dict[str, Any]] = {}
    for plugin in plugins:
        if not plugin.enabled:
            continue
        srv = await load_plugin_lsp_servers(plugin, errs)
        if srv:
            plugin.lsp_servers = srv
            scoped = add_plugin_scope_to_lsp_servers(srv, plugin.name)
            all_servers.update(scoped)
            logger.debug(
                "Loaded %s LSP servers from plugin %s",
                len(srv),
                plugin.name,
            )
    return all_servers


__all__ = [
    "add_plugin_scope_to_lsp_servers",
    "extract_lsp_servers_from_plugins",
    "get_plugin_lsp_servers",
    "load_plugin_lsp_servers",
    "load_plugin_options",
    "resolve_plugin_lsp_environment",
]
