"""Exit plan mode v2 tool. Migrated from tools/ExitPlanModeTool/ExitPlanModeV2Tool.ts (schema subset)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import EXIT_PLAN_MODE_V2_TOOL_NAME
from .prompt_definitions import EXIT_PLAN_MODE_V2_TOOL_PROMPT


@dataclass
class AllowedPrompt:
    """Prompt-based permission entry when exiting plan mode."""

    tool: str
    prompt: str


@dataclass
class ExitPlanModeV2Input:
    """Input for ExitPlanMode v2."""

    allowed_prompts: list[AllowedPrompt] = field(default_factory=list)
    plan: str | None = None
    plan_file_path: str | None = None


@dataclass
class ExitPlanModeV2Output:
    """Output from ExitPlanMode v2."""

    plan: str | None
    is_agent: bool
    file_path: str | None = None


class ExitPlanModeV2ToolDef(Tool[dict[str, Any], dict[str, Any]]):
    """Signal plan completion and request user approval (plan mode v2)."""

    @property
    def name(self) -> str:
        return EXIT_PLAN_MODE_V2_TOOL_NAME

    @property
    def search_hint(self) -> str | None:
        return "exit plan mode and request approval"

    async def description(self) -> str:
        return "Exit plan mode after writing the plan file and request user approval."

    async def prompt(self) -> str:
        return EXIT_PLAN_MODE_V2_TOOL_PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
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
                "plan": {"type": "string"},
                "plan_file_path": {"type": "string"},
            },
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan": {"type": ["string", "null"]},
                "is_agent": {"type": "boolean"},
                "file_path": {"type": "string"},
            },
            "required": ["plan", "is_agent"],
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = input, context
        return ToolResult(
            success=True,
            output={"plan": None, "is_agent": False},
        )
