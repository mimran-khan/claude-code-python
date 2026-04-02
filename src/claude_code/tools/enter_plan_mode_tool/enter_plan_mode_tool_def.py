"""Enter plan mode tool. Migrated from tools/EnterPlanModeTool/EnterPlanModeTool.ts."""

from __future__ import annotations

from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import ENTER_PLAN_MODE_TOOL_NAME
from .prompt_builder import get_enter_plan_mode_tool_prompt


class EnterPlanModeToolDef(Tool[dict[str, Any], dict[str, Any]]):
    """Transition session into plan mode."""

    @property
    def name(self) -> str:
        return ENTER_PLAN_MODE_TOOL_NAME

    @property
    def search_hint(self) -> str | None:
        return "switch to plan mode to design an approach before coding"

    async def description(self) -> str:
        return "Requests permission to enter plan mode for complex tasks requiring exploration and design"

    async def prompt(self) -> str:
        return get_enter_plan_mode_tool_prompt()

    def get_input_schema(self) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": False, "properties": {}}

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = input, context
        return ToolResult(success=True, output={"message": "Entered plan mode (stub)"})
