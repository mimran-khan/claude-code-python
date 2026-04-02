"""
Dedupe MCP client connections by name.

Migrated from: hooks/useMergedClients.ts
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def merge_clients(
    initial_clients: Sequence[Mapping[str, object]] | None,
    mcp_clients: Sequence[Mapping[str, object]] | None,
) -> list[Mapping[str, object]]:
    if initial_clients and mcp_clients and len(mcp_clients) > 0:
        merged: dict[str, Mapping[str, object]] = {}
        for c in initial_clients:
            name = str(c.get("name", ""))
            merged[name] = c
        for c in mcp_clients:
            name = str(c.get("name", ""))
            merged[name] = c
        return list(merged.values())
    return list(initial_clients or [])
