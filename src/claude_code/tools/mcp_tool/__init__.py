"""MCP Tool for calling Model Context Protocol tools (TS: tools/MCPTool/)."""

from .mcp_tool import MCP_TOOL_NAME, MCPTool

# Naming parity with PascalCase `McpTool` in migration docs
McpTool = MCPTool

__all__ = ["MCPTool", "McpTool", "MCP_TOOL_NAME"]
