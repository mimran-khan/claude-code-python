"""
Cron list tool.

List scheduled tasks.

Migrated from: tools/ScheduleCronTool/CronListTool.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult

CRON_LIST_TOOL_NAME = "CronList"


@dataclass
class CronTask:
    """A scheduled cron task."""

    id: str
    cron: str
    prompt: str
    human_schedule: str
    recurring: bool
    durable: bool
    next_run: str | None = None


class CronListTool(Tool):
    """
    Tool for listing scheduled tasks.
    """

    name = CRON_LIST_TOOL_NAME
    description = "List all scheduled tasks"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(
        self,
        input_data: dict[str, Any],
        context: Any,
    ) -> ToolResult:
        """Execute the cron list tool."""
        # In a full implementation, this would fetch from task storage
        tasks: list[CronTask] = []

        if not tasks:
            return ToolResult(
                output="No scheduled tasks found.",
            )

        lines = ["Scheduled Tasks:", ""]

        for task in tasks:
            lines.append(f"- {task.id}: {task.human_schedule}")
            lines.append(f"  Prompt: {task.prompt[:50]}...")
            if task.next_run:
                lines.append(f"  Next run: {task.next_run}")

        return ToolResult(
            output="\n".join(lines),
            data=[
                {
                    "id": t.id,
                    "cron": t.cron,
                    "prompt": t.prompt,
                    "humanSchedule": t.human_schedule,
                    "recurring": t.recurring,
                    "durable": t.durable,
                }
                for t in tasks
            ],
        )
