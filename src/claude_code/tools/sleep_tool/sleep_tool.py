"""Sleep tool implementation."""

import asyncio
from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .prompt import DESCRIPTION, SLEEP_TOOL_NAME


@dataclass
class SleepInput:
    """Input for sleep tool."""

    duration_ms: int
    reason: str | None = None


@dataclass
class SleepOutput:
    """Output from sleep tool."""

    slept_ms: int
    interrupted: bool = False
    reason: str | None = None


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "duration_ms": {
            "type": "integer",
            "minimum": 0,
            "maximum": 3600000,  # Max 1 hour
            "description": "Duration to sleep in milliseconds",
        },
        "reason": {
            "type": "string",
            "description": "Optional reason for sleeping",
        },
    },
    "required": ["duration_ms"],
}


class SleepTool(Tool):
    """Tool for sleeping/waiting."""

    name = SLEEP_TOOL_NAME
    description = DESCRIPTION
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[SleepOutput]:
        """Execute the sleep."""
        duration_ms = input_data.get("duration_ms", 0)
        reason = input_data.get("reason")

        # Cap at 1 hour
        duration_ms = min(duration_ms, 3600000)

        # Sleep in chunks to allow for interruption
        chunk_ms = 1000  # 1 second chunks
        slept_ms = 0
        interrupted = False

        while slept_ms < duration_ms:
            remaining = duration_ms - slept_ms
            sleep_chunk = min(chunk_ms, remaining)

            try:
                await asyncio.sleep(sleep_chunk / 1000)
                slept_ms += sleep_chunk
            except asyncio.CancelledError:
                interrupted = True
                break

        return ToolResult(
            data=SleepOutput(
                slept_ms=slept_ms,
                interrupted=interrupted,
                reason=reason,
            )
        )

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        """Get a summary of the tool use."""
        duration_ms = input_data.get("duration_ms", 0)
        reason = input_data.get("reason", "")

        if duration_ms < 1000:
            duration_str = f"{duration_ms}ms"
        elif duration_ms < 60000:
            duration_str = f"{duration_ms / 1000:.1f}s"
        else:
            duration_str = f"{duration_ms / 60000:.1f}m"

        if reason:
            return f"Sleep({duration_str}: {reason[:30]})"
        return f"Sleep({duration_str})"
