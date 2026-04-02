"""
Desktop / GUI automation placeholder.

No `tools/DesktopTool` exists in this workspace snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .constants import DESKTOP_TOOL_NAME


@dataclass
class DesktopToolOutput:
    ok: bool
    detail: str


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action": {"type": "string", "description": "Desktop action identifier."},
        "payload": {"type": "object", "description": "Action-specific parameters."},
    },
    "required": ["action"],
}


class DesktopTool(Tool):
    name = DESKTOP_TOOL_NAME
    description = "Desktop automation (not implemented in this Python port)."
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = False
    user_facing_name = DESKTOP_TOOL_NAME

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[DesktopToolOutput]:
        _ = context, progress_callback
        # TODO: Bridge to OS automation (AppleScript, accessibility APIs, etc.) if product adds this tool.
        action = input_data.get("action", "")
        return ToolResult(
            data=DesktopToolOutput(
                ok=False,
                detail=f"DesktopTool stub: action {action!r} not implemented.",
            ),
        )
