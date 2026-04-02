"""Enter Worktree tool implementation."""

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

ENTER_WORKTREE_TOOL_NAME = "enter_worktree"


@dataclass
class EnterWorktreeOutput:
    """Output from enter worktree."""

    success: bool
    worktree_path: str | None = None
    branch: str | None = None
    message: str = ""
    error: str | None = None


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "branch": {
            "type": "string",
            "description": "Branch name for the worktree",
        },
        "path": {
            "type": "string",
            "description": "Path for the worktree",
        },
        "create_branch": {
            "type": "boolean",
            "description": "Create the branch if it doesn't exist",
        },
    },
    "required": ["branch"],
}


class EnterWorktreeTool(Tool):
    """Tool for entering a git worktree."""

    name = ENTER_WORKTREE_TOOL_NAME
    description = "Enter a git worktree for isolated work"
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = False

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[EnterWorktreeOutput]:
        """Enter worktree."""
        input_data.get("branch", "")
        input_data.get("path", "")
        input_data.get("create_branch", False)

        # In full implementation, would:
        # 1. Check if git repo
        # 2. Create worktree
        # 3. Update cwd

        return ToolResult(
            data=EnterWorktreeOutput(
                success=False,
                error="Worktree creation not implemented (stub)",
            )
        )
