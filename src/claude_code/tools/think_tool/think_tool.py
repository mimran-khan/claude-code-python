"""
Think tool — captures planning text (structured output channel).

No dedicated TypeScript file in leak; common in agent toolkits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .prompt_text import DESCRIPTION, PROMPT, THINK_TOOL_NAME


@dataclass
class ThinkInput:
    thought: str


@dataclass
class ThinkOutput:
    recorded: bool
    length_chars: int


class ThinkTool(Tool[dict[str, Any], ThinkOutput]):
    @property
    def name(self) -> str:
        return THINK_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "planning, reasoning"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "thought": {"type": "string", "description": "Reasoning to record"},
            },
            "required": ["thought"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "recorded": {"type": "boolean"},
                "length_chars": {"type": "integer"},
            },
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        thought = str(input.get("thought", "")).strip()
        if not thought:
            return ToolResult(success=False, error="thought is required", error_code=1)
        bucket = context.read_file_state.setdefault("think_trace", [])
        if isinstance(bucket, list):
            bucket.append(thought[:50_000])
        return ToolResult(
            success=True,
            output=ThinkOutput(recorded=True, length_chars=len(thought)),
        )
