"""
Static MCP tool identifiers and overrides (client fills description/prompt).

Migrated from: tools/MCPTool/MCPTool.ts + tools/MCPTool/prompt.ts
"""

from __future__ import annotations

# Placeholder strings — TS notes real values overridden in mcpClient.ts
MCP_TOOL_NAME_DEFAULT: str = "mcp"
MCP_DESCRIPTION_OVERRIDE: str = ""
MCP_PROMPT_OVERRIDE: str = ""

MCP_USER_FACING_NAME: str = "mcp"
MCP_IS_OPEN_WORLD_DEFAULT: bool = False
