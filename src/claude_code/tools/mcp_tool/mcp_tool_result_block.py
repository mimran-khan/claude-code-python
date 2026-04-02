"""
Map MCP tool content to Anthropic tool_result block params.

Migrated from: tools/MCPTool/MCPTool.ts (mapToolResultToToolResultBlockParam)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResultBlockParam:
    """Minimal tool_result block for API compatibility."""

    tool_use_id: str
    type: str = "tool_result"
    content: str | Sequence[dict[str, Any]] = ""
    is_error: bool = False


def map_mcp_content_to_tool_result(
    content: str | Sequence[dict[str, Any]],
    tool_use_id: str,
    *,
    is_error: bool = False,
) -> ToolResultBlockParam:
    """Build tool_result block from MCP string or structured content."""
    return ToolResultBlockParam(
        tool_use_id=tool_use_id,
        content=content,
        is_error=is_error,
    )
