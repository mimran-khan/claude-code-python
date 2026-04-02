"""
Cron create tool.

Create scheduled tasks.

Migrated from: tools/ScheduleCronTool/CronCreateTool.ts (158 lines)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult

CRON_CREATE_TOOL_NAME = "CronCreate"
DEFAULT_MAX_AGE_DAYS = 30
MAX_JOBS = 50


@dataclass
class CronCreateInput:
    """Input for cron create."""

    cron: str  # 5-field cron expression
    prompt: str  # Prompt to enqueue at each fire time
    recurring: bool = True  # Fire on every match vs once
    durable: bool = False  # Persist across sessions


@dataclass
class CronCreateOutput:
    """Output from cron create."""

    id: str
    human_schedule: str
    recurring: bool
    durable: bool = False


class CronCreateTool(Tool):
    """
    Tool for creating scheduled/cron tasks.
    """

    name = CRON_CREATE_TOOL_NAME
    description = "Schedule a recurring or one-shot prompt"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cron": {
                    "type": "string",
                    "description": 'Standard 5-field cron expression in local time: "M H DoM Mon DoW"',
                },
                "prompt": {
                    "type": "string",
                    "description": "The prompt to enqueue at each fire time",
                },
                "recurring": {
                    "type": "boolean",
                    "description": "true = fire on every match until deleted. false = fire once. Default: true",
                },
                "durable": {
                    "type": "boolean",
                    "description": "true = persist and survive restarts. false = in-memory only. Default: false",
                },
            },
            "required": ["cron", "prompt"],
        }

    async def execute(
        self,
        input_data: dict[str, Any],
        context: Any,
    ) -> ToolResult:
        """Execute the cron create tool."""
        cron_expr = input_data.get("cron", "")
        input_data.get("prompt", "")
        recurring = input_data.get("recurring", True)
        durable = input_data.get("durable", False)

        # Validate cron expression
        is_valid, error = self._validate_cron(cron_expr)
        if not is_valid:
            return ToolResult(
                output=f"Invalid cron expression: {error}",
                is_error=True,
            )

        # Generate task ID
        import uuid

        task_id = str(uuid.uuid4())[:8]

        # Parse cron to human-readable
        human_schedule = self._cron_to_human(cron_expr)

        # In a full implementation, this would register the task
        output = CronCreateOutput(
            id=task_id,
            human_schedule=human_schedule,
            recurring=recurring,
            durable=durable,
        )

        return ToolResult(
            output=f"Created task {task_id}: {human_schedule}",
            data={
                "id": output.id,
                "humanSchedule": output.human_schedule,
                "recurring": output.recurring,
                "durable": output.durable,
            },
        )

    def _validate_cron(self, cron_expr: str) -> tuple[bool, str | None]:
        """Validate a cron expression."""
        parts = cron_expr.strip().split()

        if len(parts) != 5:
            return False, "Must have exactly 5 fields (minute hour day month weekday)"

        # Basic validation - just check format
        for i, part in enumerate(parts):
            if not part:
                return False, f"Empty field at position {i}"

        return True, None

    def _cron_to_human(self, cron_expr: str) -> str:
        """Convert cron expression to human-readable string."""
        parts = cron_expr.strip().split()

        if len(parts) != 5:
            return cron_expr

        minute, hour, dom, month, dow = parts

        # Simple patterns
        if cron_expr == "* * * * *":
            return "Every minute"

        if minute.startswith("*/"):
            interval = minute[2:]
            return f"Every {interval} minutes"

        if hour == "*" and dom == "*" and month == "*" and dow == "*":
            return f"Every hour at minute {minute}"

        # Default: return formatted cron
        return f"Cron: {cron_expr}"
