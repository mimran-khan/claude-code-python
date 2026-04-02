"""Exit Plan Mode tool (v2-style) implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .constants import EXIT_PLAN_MODE_TOOL_NAME


@dataclass
class AllowedPrompt:
    """Prompt-based permission entry when exiting plan mode."""

    tool: Literal["Bash"] = "Bash"
    prompt: str = ""


@dataclass
class ExitPlanModeInput:
    allowed_prompts: list[AllowedPrompt] = field(default_factory=list)
    plan: str | None = None
    plan_file_path: str | None = None


@dataclass
class ExitPlanModeOutput:
    plan: str | None
    is_agent: bool
    file_path: str | None = None
    has_task_tool: bool | None = None
    plan_was_edited: bool | None = None
    awaiting_leader_approval: bool | None = None
    request_id: str | None = None


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "allowed_prompts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tool": {"type": "string", "enum": ["Bash"]},
                    "prompt": {"type": "string"},
                },
                "required": ["tool", "prompt"],
            },
        },
    },
}


class ExitPlanModeTool(Tool):
    """Signals completion of planning and requests approval to leave plan mode."""

    name = EXIT_PLAN_MODE_TOOL_NAME
    description = "Prompts the user to exit plan mode and start coding"
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[ExitPlanModeOutput]:
        is_agent = bool(context.agent_id)
        plan = input_data.get("plan")
        file_path = input_data.get("plan_file_path")
        input_plan = plan if isinstance(plan, str) else None
        return ToolResult(
            data=ExitPlanModeOutput(
                plan=input_plan,
                is_agent=is_agent,
                file_path=file_path if isinstance(file_path, str) else None,
                has_task_tool=False,
                plan_was_edited=input_plan is not None,
            )
        )
