"""MCP Tool implementation for calling Model Context Protocol tools."""

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

MCP_TOOL_NAME = "CallMcpTool"

DESCRIPTION = "Call an MCP tool"

PROMPT = """Call a tool from an MCP (Model Context Protocol) server.

This tool allows you to execute tools provided by connected MCP servers.
The tool name should be in the format: server_name/tool_name

Arguments will be passed directly to the MCP tool."""


@dataclass
class MCPProgress:
    """Progress for MCP operations."""

    type: str = "mcp"
    status: str = ""
    server_name: str | None = None
    tool_name: str | None = None


@dataclass
class MCPOutput:
    """Output from MCP tool."""

    result: str
    server_name: str | None = None
    tool_name: str | None = None


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "server": {
            "type": "string",
            "description": "The MCP server name",
        },
        "toolName": {
            "type": "string",
            "description": "The tool name to call",
        },
        "arguments": {
            "type": "object",
            "description": "Arguments to pass to the tool",
        },
    },
    "required": ["server", "toolName"],
}


class MCPTool(Tool):
    """Tool for calling MCP tools."""

    name = MCP_TOOL_NAME
    description = DESCRIPTION
    input_schema = INPUT_SCHEMA
    is_read_only = False  # MCP tools may have side effects
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[MCPOutput]:
        """Execute the MCP tool call."""
        server_name = input_data.get("server", "")
        tool_name = input_data.get("toolName", "")
        input_data.get("arguments", {})

        # In full implementation, this would:
        # 1. Find the MCP client for the server
        # 2. Call the tool with arguments
        # 3. Return the result

        # Stub implementation
        return ToolResult(
            data=MCPOutput(
                result=f"MCP tool {server_name}/{tool_name} called (stub)",
                server_name=server_name,
                tool_name=tool_name,
            )
        )

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        """Get a summary of the tool use."""
        server = input_data.get("server", "?")
        tool = input_data.get("toolName", "?")
        return f"MCP({server}/{tool})"
