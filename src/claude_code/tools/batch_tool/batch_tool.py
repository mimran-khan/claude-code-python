"""
Parallel / batch tool invocation placeholder.

No `tools/BatchTool` directory exists in this workspace snapshot; this module
reserves the name and documents integration points.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .constants import BATCH_TOOL_NAME


@dataclass
class BatchToolOutput:
    message: str
    tool_uses: list[dict[str, Any]]


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "tool_uses": {
            "type": "array",
            "description": "Ordered tool calls to run (host-defined shape).",
            "items": {"type": "object"},
        },
    },
    "required": ["tool_uses"],
}


class BatchTool(Tool):
    name = BATCH_TOOL_NAME
    description = "Run multiple tool calls in a single batch (not wired in this port)."
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = False
    user_facing_name = BATCH_TOOL_NAME

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[BatchToolOutput]:
        _ = context, progress_callback
        # TODO: Integrate with services that support API batching / parallel tool_use.
        uses = input_data.get("tool_uses")
        if not isinstance(uses, list):
            uses = []
        return ToolResult(
            data=BatchToolOutput(
                message="BatchTool is a stub in claude-code-python; execute tools individually.",
                tool_uses=uses,
            ),
        )
