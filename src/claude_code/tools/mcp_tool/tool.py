"""
MCP Tool Implementation.

Call Model Context Protocol tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult

MCP_TOOL_NAME = "CallMcpTool"

DESCRIPTION = "Call an MCP tool by server identifier and tool name."


class MCPToolInput(BaseModel):
    """Input parameters for MCP tool."""

    server: str = Field(
        ...,
        description="Identifier of the MCP server hosting the tool.",
    )
    tool_name: str = Field(
        ...,
        alias="toolName",
        description="Name of the MCP tool to invoke.",
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the MCP tool.",
    )


@dataclass
class MCPToolSuccess:
    """Successful MCP tool result."""

    type: Literal["success"] = "success"
    result: Any = None


@dataclass
class MCPToolError:
    """Failed MCP tool result."""

    type: Literal["error"] = "error"
    error: str = ""


MCPToolOutput = MCPToolSuccess | MCPToolError


class MCPTool(Tool[MCPToolInput, MCPToolOutput]):
    """
    Tool for calling MCP tools.
    """

    @property
    def name(self) -> str:
        return MCP_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": "Identifier of the MCP server.",
                },
                "toolName": {
                    "type": "string",
                    "description": "Name of the MCP tool to invoke.",
                },
                "arguments": {
                    "type": "object",
                    "description": "Arguments to pass to the tool.",
                },
            },
            "required": ["server", "toolName"],
        }

    def is_read_only(self, input_data: MCPToolInput) -> bool:
        return False  # MCP tools may have side effects

    async def call(
        self,
        input_data: MCPToolInput,
        context: Any,
    ) -> ToolResult[MCPToolOutput]:
        """Execute the MCP tool operation."""
        # Placeholder - actual implementation would call MCP server
        return ToolResult(
            success=False,
            output=MCPToolError(
                error="MCP tool execution requires MCP server integration.",
            ),
        )

    def user_facing_name(self, input_data: MCPToolInput | None = None) -> str:
        if input_data:
            return f"MCP:{input_data.tool_name}"
        return "MCP Tool"
