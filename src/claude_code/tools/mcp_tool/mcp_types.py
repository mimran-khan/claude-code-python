"""
Typed shapes for generic MCP tool invocation.

Migrated from: tools/MCPTool/MCPTool.ts (schema intent)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class McpToolCallInput:
    """Passthrough arguments for a specific MCP tool (server fills schema)."""

    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class McpToolCallOutput:
    """String result from MCP execution (TS outputSchema is z.string())."""

    data: str
