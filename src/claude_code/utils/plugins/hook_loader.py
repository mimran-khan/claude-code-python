"""
Register hook matchers from enabled plugins into global state.

Migrated from: utils/plugins/loadPluginHooks.ts
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

from ...bootstrap.state import (
    clear_registered_plugin_hooks,
    get_registered_hooks,
    register_hook_callbacks,
)
from ...types.plugin import LoadedPlugin, PluginLoadResult
from ..settings import change_detector as settings_change_detector_module
from ..settings.settings import get_merged_settings, get_settings_for_source

logger = logging.getLogger(__name__)


@dataclass
class PluginHookMatcherRecord:
    """One plugin hook matcher row (mirrors TS ``PluginHookMatcher`` payload to state)."""

    matcher: Any
    hooks: list[Any]
    plugin_root: str
    plugin_name: str
    plugin_id: str

    def to_callback_dict(self) -> dict[str, Any]:
        return {
            "matcher": self.matcher,
            "hooks": self.hooks,
            "pluginRoot": self.plugin_root,
            "pluginName": self.plugin_name,
            "pluginId": self.plugin_id,
        }


_HOOK_LOAD_LOCK = asyncio.Lock()
_HOOK_LOAD_DONE = False

_hot_reload_subscribed = False
_last_plugin_settings_snapshot: str | None = None


def _empty_plugin_load() -> PluginLoadResult:
    return PluginLoadResult(enabled=[], disabled=[], errors=[])


async def _load_all_plugins_cache_only() -> PluginLoadResult:
    try:
        from .plugin_loader import load_all_plugins_cache_only as fn

        return await fn()
    except (ImportError, AttributeError):
        return _empty_plugin_load()


def _all_hook_events() -> list[str]:
    return [
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "PermissionDenied",
        "Notification",
        "UserPromptSubmit",
        "SessionStart",
        "SessionEnd",
        "Stop",
        "StopFailure",
        "SubagentStart",
        "SubagentStop",
        "PreCompact",
        "PostCompact",
        "PermissionRequest",
        "Setup",
        "TeammateIdle",
        "TaskCreated",
        "TaskCompleted",
        "Elicitation",
        "ElicitationResult",
        "ConfigChange",
        "WorktreeCreate",
        "WorktreeRemove",
        "InstructionsLoaded",
        "CwdChanged",
        "FileChanged",
    ]


def _empty_matchers() -> dict[str, list[dict[str, Any]]]:
    return {ev: [] for ev in _all_hook_events()}


def convert_plugin_hooks_to_matchers(plugin: LoadedPlugin) -> dict[str, list[dict[str, Any]]]:
    out = _empty_matchers()
    cfg = plugin.hooks_config
    if not cfg:
        return out
    for event, matchers in cfg.items():
        if event not in out or not isinstance(matchers, list):
            continue
        for matcher in matchers:
            if not isinstance(matcher, dict):
                continue
            hooks = matcher.get("hooks") or []
            if not hooks:
                continue
            rec = PluginHookMatcherRecord(
                matcher=matcher.get("matcher"),
                hooks=hooks,
                plugin_root=plugin.path,
                plugin_name=plugin.name,
                plugin_id=plugin.source,
            )
            out[event].append(rec.to_callback_dict())
    return out


async def load_plugin_hooks() -> None:
    global _HOOK_LOAD_DONE
    async with _HOOK_LOAD_LOCK:
        if _HOOK_LOAD_DONE:
            return
        result = await _load_all_plugins_cache_only()
        enabled = result.enabled
        all_hooks = _empty_matchers()
        for plugin in enabled:
            if not plugin.hooks_config:
                continue
            logger.debug("Loading hooks from plugin: %s", plugin.name)
            matchers = convert_plugin_hooks_to_matchers(plugin)
            for ev in all_hooks:
                all_hooks[ev].extend(matchers.get(ev, []))
        clear_registered_plugin_hooks()
        register_hook_callbacks(all_hooks)
        total = sum(len(m.get("hooks", [])) for matchers in all_hooks.values() for m in matchers)
        logger.debug("Registered %s hooks from %s plugins", total, len(enabled))
        _HOOK_LOAD_DONE = True


def clear_plugin_hook_cache() -> None:
    global _HOOK_LOAD_DONE
    _HOOK_LOAD_DONE = False


async def prune_removed_plugin_hooks() -> None:
    current = get_registered_hooks()
    if not current:
        return
    result = await _load_all_plugins_cache_only()
    enabled_roots = {p.path for p in result.enabled}
    current2 = get_registered_hooks()
    if not current2:
        return
    survivors: dict[str, list[Any]] = {}
    for event, matchers in current2.items():
        kept = [m for m in matchers if isinstance(m, dict) and m.get("pluginRoot") in enabled_roots]
        if kept:
            survivors[event] = kept
    clear_registered_plugin_hooks()
    register_hook_callbacks(survivors)


def reset_hot_reload_state() -> None:
    global _hot_reload_subscribed, _last_plugin_settings_snapshot
    _hot_reload_subscribed = False
    _last_plugin_settings_snapshot = None


def get_plugin_affecting_settings_snapshot() -> str:
    merged = get_merged_settings()
    policy = get_settings_for_source("policySettings") or {}

    def sort_keys(o: Any) -> dict[str, Any]:
        if not isinstance(o, dict):
            return {}
        return dict(sorted(o.items()))

    payload = {
        "enabledPlugins": sort_keys(merged.get("enabledPlugins")),
        "extraKnownMarketplaces": sort_keys(merged.get("extraKnownMarketplaces")),
        "strictKnownMarketplaces": policy.get("strictKnownMarketplaces") or [],
        "blockedMarketplaces": policy.get("blockedMarketplaces") or [],
    }
    return json.dumps(payload, sort_keys=True)


def setup_plugin_hook_hot_reload() -> None:
    global _hot_reload_subscribed, _last_plugin_settings_snapshot
    if _hot_reload_subscribed:
        return
    _hot_reload_subscribed = True
    _last_plugin_settings_snapshot = get_plugin_affecting_settings_snapshot()

    def _on_settings_changed() -> None:
        global _last_plugin_settings_snapshot
        new_snap = get_plugin_affecting_settings_snapshot()
        if new_snap == _last_plugin_settings_snapshot:
            logger.debug(
                "Plugin hooks: skipping reload, plugin-affecting settings unchanged",
            )
            return
        _last_plugin_settings_snapshot = new_snap
        logger.debug("Plugin hooks: reloading due to plugin-affecting settings change")
        try:
            from .plugin_loader import clear_plugin_cache
        except ImportError:

            def clear_plugin_cache(_reason: str) -> None:
                return None

        clear_plugin_cache("hook_loader: plugin-affecting settings changed")
        clear_plugin_hook_cache()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.debug("Plugin hooks: no running loop for reload task")
        else:
            loop.create_task(load_plugin_hooks())

    settings_change_detector_module.settings_change_detector["subscribe"](
        _on_settings_changed,
    )


__all__ = [
    "PluginHookMatcherRecord",
    "clear_plugin_hook_cache",
    "convert_plugin_hooks_to_matchers",
    "get_plugin_affecting_settings_snapshot",
    "load_plugin_hooks",
    "prune_removed_plugin_hooks",
    "reset_hot_reload_state",
    "setup_plugin_hook_hot_reload",
]
