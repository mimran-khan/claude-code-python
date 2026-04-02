"""
Permission decision shape for MCP tool (passthrough / ask user).

Migrated from: tools/MCPTool/MCPTool.ts (checkPermissions)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PermissionBehavior = Literal["passthrough", "allow", "deny", "ask"]


@dataclass
class McpPermissionResult:
    """Result of MCP permission check."""

    behavior: PermissionBehavior
    message: str = ""


def mcp_default_permission() -> McpPermissionResult:
    """TS returns passthrough with fixed message."""
    return McpPermissionResult(
        behavior="passthrough",
        message="MCPTool requires permission.",
    )
