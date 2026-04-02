"""
Initial plugin load orchestration hooks.

Migrated from: hooks/useManagePlugins.ts (call out to existing Python plugin loaders).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class PluginLoadMetrics:
    enabled_count: int
    disabled_count: int
    error_count: int


async def run_initial_plugin_load_simple(
    *,
    load_all_plugins: Callable[[], Awaitable[tuple[list[Any], list[Any], list[Any]]]],
    on_loaded: Callable[[list[Any], list[Any], list[Any]], Awaitable[None] | None] | None = None,
) -> PluginLoadMetrics:
    enabled, disabled, errors = await load_all_plugins()
    if on_loaded is not None:
        r = on_loaded(enabled, disabled, errors)
        if r is not None:
            await r
    return PluginLoadMetrics(
        enabled_count=len(enabled),
        disabled_count=len(disabled),
        error_count=len(errors),
    )


def notify_plugins_need_reload(add_notification: Callable[[dict[str, Any]], None]) -> None:
    add_notification(
        {
            "key": "plugin-reload-pending",
            "text": "Plugins changed. Run /reload-plugins to activate.",
            "color": "suggestion",
        }
    )
