"""
Merge built-in and MCP slash commands with dedupe by name.

Migrated from: hooks/useMergedCommands.ts
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def merge_commands(
    initial_commands: Sequence[Mapping[str, object]],
    mcp_commands: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    if len(mcp_commands) == 0:
        return list(initial_commands)
    merged: dict[str, Mapping[str, object]] = {}
    for c in initial_commands:
        merged[str(c.get("name", ""))] = c
    for c in mcp_commands:
        merged[str(c.get("name", ""))] = c
    return list(merged.values())
