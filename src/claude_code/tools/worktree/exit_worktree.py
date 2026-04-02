"""Exit Worktree tool implementation."""

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

EXIT_WORKTREE_TOOL_NAME = "exit_worktree"


@dataclass
class ExitWorktreeOutput:
    """Output from exit worktree."""

    success: bool
    previous_path: str | None = None
    message: str = ""
    error: str | None = None


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "cleanup": {
            "type": "boolean",
            "description": "Remove the worktree after exiting",
        },
    },
}


class ExitWorktreeTool(Tool):
    """Tool for exiting a git worktree."""

    name = EXIT_WORKTREE_TOOL_NAME
    description = "Exit the current git worktree"
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = False

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[ExitWorktreeOutput]:
        """Exit worktree."""
        input_data.get("cleanup", False)

        # In full implementation, would:
        # 1. Check if in worktree
        # 2. Return to original directory
        # 3. Optionally cleanup worktree

        return ToolResult(
            data=ExitWorktreeOutput(
                success=False,
                error="Not in a worktree (stub)",
            )
        )
