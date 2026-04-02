"""Load MCP server configs from plugins. Migrated from mcpPluginIntegration.ts (minimal)."""

from __future__ import annotations

import json
import os
from typing import Any

from ...types.plugin import LoadedPlugin
from ..debug import log_for_debugging
from ..errors import is_enoent


async def load_plugin_mcp_servers(
    plugin: LoadedPlugin,
    errors: list[Any] | None = None,
) -> dict[str, Any] | None:
    errors = errors if errors is not None else []
    servers: dict[str, Any] = {}
    mcp_json = os.path.join(plugin.path, ".mcp.json")
    try:
        with open(mcp_json, encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            servers.update(data)
    except OSError as exc:
        if not is_enoent(exc):
            log_for_debugging(f"MCP config read error for {plugin.name}: {exc}")
            errors.append(
                {
                    "type": "mcp-config-invalid",
                    "plugin": plugin.name,
                    "serverName": ".mcp.json",
                    "validationError": str(exc),
                    "source": "plugin",
                }
            )
    except json.JSONDecodeError as exc:
        errors.append(
            {
                "type": "mcp-config-invalid",
                "plugin": plugin.name,
                "serverName": ".mcp.json",
                "validationError": str(exc),
                "source": "plugin",
            }
        )
    return servers if servers else None


__all__ = ["load_plugin_mcp_servers"]
