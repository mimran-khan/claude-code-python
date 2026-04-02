#!/usr/bin/env python3
"""
Define a small custom tool using the same ``Tool`` base class as built-ins.

Pattern: explicit JSON Schema, async ``execute``, and structured ``ToolResult``.

Run:
  python examples/custom_tool.py
"""

from __future__ import annotations

import asyncio
import random
import sys
from typing import Any

from _path_setup import ensure_src_on_path

ensure_src_on_path()

from claude_code.tools.base import Tool, ToolResult, ToolUseContext


class RollDiceTool(Tool[dict[str, Any], dict[str, Any]]):
    """
    Example tool: roll an N-sided die ``count`` times (bounded for safety).
    """

    @property
    def name(self) -> str:
        return "RollDice"

    @property
    def search_hint(self) -> str | None:
        return "roll random dice for demos"

    async def description(self) -> str:
        return "Roll dice with a configurable number of sides and rolls (demo tool)."

    async def prompt(self) -> str:
        return await self.description()

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "sides": {
                    "type": "integer",
                    "description": "Number of sides on each die (2–100).",
                    "minimum": 2,
                    "maximum": 100,
                },
                "count": {
                    "type": "integer",
                    "description": "How many dice to roll (1–20).",
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["sides", "count"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rolls": {"type": "array", "items": {"type": "integer"}},
                "total": {"type": "integer"},
            },
        }

    async def execute(self, input: dict[str, Any], context: ToolUseContext) -> ToolResult:
        try:
            sides = int(input.get("sides", 0))
            count = int(input.get("count", 0))
        except (TypeError, ValueError):
            return ToolResult(success=False, error="sides and count must be integers", error_code=1)

        if not (2 <= sides <= 100 and 1 <= count <= 20):
            return ToolResult(
                success=False,
                error="Invalid sides (2–100) or count (1–20)",
                error_code=2,
            )

        try:
            rolls = [random.randint(1, sides) for _ in range(count)]
        except Exception as exc:
            return ToolResult(success=False, error=f"RNG failed: {exc}", error_code=3)

        return ToolResult(
            success=True,
            output={"rolls": rolls, "total": sum(rolls)},
        )


async def main() -> int:
    tool = RollDiceTool()
    ctx = ToolUseContext(tool_use_id="custom-dice-demo")

    payload = {"sides": 6, "count": 3}
    try:
        v = await tool.validate_input(payload, ctx)
        if not v.get("result", False):
            print(f"validate_input rejected: {v}", file=sys.stderr)
            return 1

        result = await tool.execute(payload, ctx)
        if not result.success:
            print(f"execute failed: {result.error}", file=sys.stderr)
            return 1

        print(f"Tool {tool.name!r} output: {result.output}")

        # Show how the engine / registry would see this tool
        print("\nAnthropic-style tool definition snippet:")
        print(
            json_dumps_pretty(
                {
                    "name": tool.name,
                    "description": await tool.description(),
                    "input_schema": tool.get_input_schema(),
                }
            )
        )

    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    return 0


def json_dumps_pretty(obj: object) -> str:
    import json

    return json.dumps(obj, indent=2)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
