"""
Load agent definitions from plugins.

Migrated from: utils/plugins/loadPluginAgents.ts (minimal port).
"""

from __future__ import annotations

import asyncio
from typing import Any

from .plugin_loader import load_all_plugins_cache_only

_agent_lock = asyncio.Lock()
_cached_agents: list[Any] | None = None


async def get_plugin_agents() -> list[Any]:
    global _cached_agents
    async with _agent_lock:
        if _cached_agents is not None:
            return list(_cached_agents)
        result = await load_all_plugins_cache_only()
        agents: list[Any] = []
        for plugin in result.enabled:
            if plugin.agents_path:
                agents.append({"plugin": plugin.name, "path": plugin.agents_path})
        _cached_agents = agents
        return list(agents)


def clear_plugin_agent_cache() -> None:
    global _cached_agents
    _cached_agents = None


__all__ = ["clear_plugin_agent_cache", "get_plugin_agents"]
