"""Enter Plan Mode tool. Migrated from tools/EnterPlanModeTool/EnterPlanModeTool.ts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .constants import ENTER_PLAN_MODE_TOOL_NAME
from .prompt_text import get_enter_plan_mode_tool_prompt


@dataclass
class EnterPlanModeInput:
    """Empty strict object in TS — reserved for future flags."""

    pass


@dataclass
class EnterPlanModeOutput:
    message: str


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {},
}


class EnterPlanModeTool(Tool):
    """Tool for entering plan mode."""

    name = ENTER_PLAN_MODE_TOOL_NAME
    description = "Requests permission to enter plan mode for complex tasks requiring exploration and design"
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True
    user_facing_name = ""

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[EnterPlanModeOutput]:
        if context.agent_id:
            raise RuntimeError("EnterPlanMode tool cannot be used in agent contexts")
        msg = (
            "Entered plan mode. You should now focus on exploring the codebase "
            "and designing an implementation approach."
        )
        return ToolResult(data=EnterPlanModeOutput(message=msg))

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        return "EnterPlanMode"


def tool_documentation_prompt() -> str:
    """Full model-facing documentation (mirrors TS async prompt())."""
    return get_enter_plan_mode_tool_prompt()
