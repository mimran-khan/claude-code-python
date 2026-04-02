"""
Clear conversation / tool state (placeholder).

TS references live under services/compact (e.g. USE_API_CLEAR_TOOL_USES); there is
no standalone tools/ClearTool in this tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .constants import CLEAR_TOOL_NAME


@dataclass
class ClearToolOutput:
    cleared: bool
    detail: str


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "scope": {
            "type": "string",
            "enum": ["tool_results", "messages", "session"],
            "description": "What to clear (host-defined).",
        },
    },
}


class ClearTool(Tool):
    name = CLEAR_TOOL_NAME
    description = "Clear cached tool results or transcript state (host integration required)."
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = True
    user_facing_name = CLEAR_TOOL_NAME

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[ClearToolOutput]:
        _ = input_data, progress_callback
        # TODO: Call into compact/session service (see services/compact/apiMicrocompact.ts).
        opts = context.options or {}
        hook = opts.get("clear_session_async") if isinstance(opts, dict) else None
        if callable(hook):
            await hook()
            return ToolResult(data=ClearToolOutput(cleared=True, detail="Host clear_session_async completed."))
        return ToolResult(
            data=ClearToolOutput(
                cleared=False,
                detail="ClearTool stub: pass options['clear_session_async'] to perform clearing.",
            ),
        )
