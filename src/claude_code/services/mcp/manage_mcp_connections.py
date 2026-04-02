"""
MCP connection lifecycle orchestration for the desktop app.

The TypeScript source is ``services/mcp/useManageMCPConnections.ts`` (React hook).
That hook wires UI state, notifications, channel permissions, and cache refresh.

The Python CLI and headless flows use ``claude_code.services.mcp.client`` and
related modules directly instead of a single orchestration entry point.
"""

from __future__ import annotations

__all__: list[str] = []
