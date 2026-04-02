"""
Refresh active plugin components in a running session (Layer 3).

Migrated from: utils/plugins/refresh.ts
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ...types.plugin import LoadedPlugin, PluginError
from ..debug import log_for_debugging
from ..errors import error_message
from ..log import log_error
from .cache_utils import clear_all_caches
from .load_plugin_commands import get_plugin_commands
from .load_plugin_hooks import load_plugin_hooks
from .lsp_integration import load_plugin_lsp_servers
from .mcp_plugin_integration import load_plugin_mcp_servers
from .orphaned_plugin_filter import clear_plugin_cache_exclusions
from .plugin_loader import load_all_plugins


@dataclass
class RefreshActivePluginsResult:
    enabled_count: int = 0
    disabled_count: int = 0
    command_count: int = 0
    agent_count: int = 0
    hook_count: int = 0
    mcp_count: int = 0
    lsp_count: int = 0
    error_count: int = 0
    agent_definitions: dict[str, Any] = field(default_factory=dict)
    plugin_commands: list[Any] = field(default_factory=list)


def _plugin_error_key(e: PluginError) -> str:
    t = getattr(e, "type", "unknown")
    src = getattr(e, "source", "") or ""
    if t == "generic-error":
        return f"generic-error:{src}:{getattr(e, 'error', '')}"
    return f"{t}:{src}"


def _merge_plugin_errors(existing: list[PluginError], fresh: list[PluginError]) -> list[PluginError]:
    preserved = [
        e
        for e in existing
        if (getattr(e, "source", "") or "") == "lsp-manager" or str(getattr(e, "source", "")).startswith("plugin:")
    ]
    fresh_keys = {_plugin_error_key(e) for e in fresh}
    deduped = [e for e in preserved if _plugin_error_key(e) not in fresh_keys]
    return [*deduped, *fresh]


def _reinitialize_lsp_server_manager() -> None:
    try:
        from ...services.lsp.manager import reinitialize_lsp_server_manager
    except ImportError:
        return
    try:
        reinitialize_lsp_server_manager()
    except Exception as exc:
        log_for_debugging(f"refreshActivePlugins: reinitializeLspServerManager: {exc}")


async def _maybe_load_agent_definitions() -> dict[str, Any]:
    try:
        from ...bootstrap.state import get_original_cwd
        from ...tools.agent_tool.load_agents_dir import get_agent_definitions_with_overrides
    except ImportError:
        return {}
    try:
        return await get_agent_definitions_with_overrides(get_original_cwd())
    except Exception as exc:
        log_for_debugging(f"refreshActivePlugins: agent definitions skipped: {exc}")
        return {}


async def _count_mcp_for_plugin(
    plugin: LoadedPlugin,
    errors: list[PluginError],
) -> int:
    if plugin.mcp_servers:
        return len(plugin.mcp_servers)
    servers = await load_plugin_mcp_servers(plugin, errors)
    if servers:
        plugin.mcp_servers = servers
        return len(servers)
    return 0


async def _count_lsp_for_plugin(
    plugin: LoadedPlugin,
    errors: list[PluginError],
) -> int:
    if plugin.lsp_servers:
        return len(plugin.lsp_servers)
    servers = await load_plugin_lsp_servers(plugin, errors)
    if servers:
        plugin.lsp_servers = servers
        return len(servers)
    return 0


def _count_hooks(enabled: list[LoadedPlugin]) -> int:
    total = 0
    for p in enabled:
        cfg = p.hooks_config
        if not cfg or not isinstance(cfg, dict):
            continue
        for matchers in cfg.values():
            if not isinstance(matchers, list):
                continue
            for m in matchers:
                if isinstance(m, dict):
                    hooks = m.get("hooks") or []
                    if isinstance(hooks, list):
                        total += len(hooks)
    return total


def _make_app_state_merger(
    enabled: list[LoadedPlugin],
    disabled: list[LoadedPlugin],
    plugin_commands: list[Any],
    errors: list[PluginError],
    agent_definitions: dict[str, Any],
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def _merge(prev: dict[str, Any]) -> dict[str, Any]:
        plugins_prev = dict(prev.get("plugins") or {})
        merged_errors = _merge_plugin_errors(list(plugins_prev.get("errors") or []), errors)
        plugins_prev.update(
            {
                "enabled": enabled,
                "disabled": disabled,
                "commands": plugin_commands,
                "errors": merged_errors,
                "needsRefresh": False,
            }
        )
        mcp = dict(prev.get("mcp") or {})
        mcp["pluginReconnectKey"] = int(mcp.get("pluginReconnectKey") or 0) + 1
        out = {**prev, "plugins": plugins_prev, "mcp": mcp}
        if agent_definitions:
            out["agentDefinitions"] = agent_definitions
        return out

    return _merge


async def refresh_active_plugins(
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None] | None = None,
) -> RefreshActivePluginsResult:
    """
    Clear caches, reload plugins, commands, MCP/LSP metadata, hooks, and optionally AppState.

    Mirrors TS ``refreshActivePlugins``: sequential ``load_all_plugins`` then parallel
    commands + agents; parallel per-plugin MCP/LSP warm; merged plugin errors.
    """
    log_for_debugging("refreshActivePlugins: clearing all plugin caches")
    clear_all_caches()
    clear_plugin_cache_exclusions()

    plugin_result = await load_all_plugins()
    agent_definitions_task = asyncio.create_task(_maybe_load_agent_definitions())
    plugin_commands_task = asyncio.create_task(get_plugin_commands())
    agent_definitions, plugin_commands = await asyncio.gather(
        agent_definitions_task,
        plugin_commands_task,
    )

    enabled = plugin_result.enabled
    disabled = plugin_result.disabled
    errors = list(plugin_result.errors)

    mcp_tasks = [_count_mcp_for_plugin(p, errors) for p in enabled]
    lsp_tasks = [_count_lsp_for_plugin(p, errors) for p in enabled]
    mcp_counts = list(await asyncio.gather(*mcp_tasks)) if mcp_tasks else []
    lsp_counts = list(await asyncio.gather(*lsp_tasks)) if lsp_tasks else []
    mcp_count = sum(mcp_counts)
    lsp_count = sum(lsp_counts)

    agent_count = 0
    if isinstance(agent_definitions, dict):
        all_agents = agent_definitions.get("allAgents")
        if isinstance(all_agents, list):
            agent_count = len(all_agents)

    if set_app_state is not None:
        ad = agent_definitions if isinstance(agent_definitions, dict) else {}
        set_app_state(
            _make_app_state_merger(enabled, disabled, plugin_commands, errors, ad),
        )

    _reinitialize_lsp_server_manager()

    hook_load_failed = False
    try:
        await load_plugin_hooks()
    except Exception as exc:
        hook_load_failed = True
        log_error(exc)
        log_for_debugging(
            f"refreshActivePlugins: loadPluginHooks failed: {error_message(exc)}",
        )

    hook_count = _count_hooks(enabled)

    log_for_debugging(
        f"refreshActivePlugins: {len(enabled)} enabled, {len(plugin_commands)} commands, "
        f"{agent_count} agents, {hook_count} hooks, {mcp_count} MCP, {lsp_count} LSP",
    )

    return RefreshActivePluginsResult(
        enabled_count=len(enabled),
        disabled_count=len(disabled),
        command_count=len(plugin_commands),
        agent_count=agent_count,
        hook_count=hook_count,
        mcp_count=mcp_count,
        lsp_count=lsp_count,
        error_count=len(errors) + (1 if hook_load_failed else 0),
        agent_definitions=agent_definitions if isinstance(agent_definitions, dict) else {},
        plugin_commands=plugin_commands,
    )


__all__ = ["RefreshActivePluginsResult", "refresh_active_plugins"]
