"""
MCP tool passthrough input/output shapes.

Migrated from: tools/MCPTool/MCPTool.ts (lazySchema z.object passthrough / string output)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass
class McpCallInput:
    """Arguments for a single MCP tool invocation (schema defined by server)."""

    server: str = ""
    tool_name: str = ""
    arguments: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def merged_payload(self) -> dict[str, Any]:
        """Flatten into one dict for wire/API use."""
        out: dict[str, Any] = {"server": self.server, "toolName": self.tool_name}
        out.update(dict(self.arguments))
        out.update(dict(self.extra))
        return out


@dataclass
class McpCallOutput:
    """MCP tool returns string result in TS; we keep structured optional fields."""

    data: str
    server_name: str | None = None
    tool_name: str | None = None


MCP_MAX_RESULT_SIZE_CHARS: int = 100_000
