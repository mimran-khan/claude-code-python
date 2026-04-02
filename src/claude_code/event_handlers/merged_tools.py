"""
Assemble tool pool: built-in + MCP with permission context.

Migrated from: hooks/useMergedTools.ts
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ..core.tool import Tool
from ..tools_assembly import assemble_tool_pool


def merge_mcp_tools(
    initial_tools: Sequence[Tool],
    mcp_tools: Sequence[Tool],
    tool_permission_context: Mapping[str, Any],
) -> list[Tool]:
    """
    Combine pools; ``tool_permission_context`` is accepted for API parity (TS assembleToolPool).

    Extend with merge-and-filter by permission mode when Python tool_pool matches TS.
    """
    _ = tool_permission_context
    assembled = assemble_tool_pool(mcp_tools)
    merged: dict[str, Tool] = {}
    for t in assembled:
        merged[t.name] = t
    for t in initial_tools:
        merged[t.name] = t
    return list(merged.values())
