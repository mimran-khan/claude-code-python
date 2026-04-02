"""EnterPlanMode documentation. Migrated from tools/EnterPlanModeTool/prompt.ts."""

from __future__ import annotations

import os

from ..plan_mode.prompt import ASK_USER_QUESTION_TOOL_NAME
from ..plan_mode.prompt import get_enter_plan_mode_tool_prompt as _external_default


def _ant_prompt() -> str:
    return f"""Use this tool when a task has genuine ambiguity about the right approach and getting user input before coding would prevent significant rework. This tool transitions you into plan mode where you can explore the codebase and design an implementation approach for user approval.

## When to Use This Tool

Plan mode is valuable when the implementation approach is genuinely unclear. Use it for significant architectural ambiguity, unclear requirements, or high-impact restructuring.

## When NOT to Use This Tool

Skip plan mode when you can reasonably infer the right approach, or for research tasks (use the Agent tool instead). When in doubt, prefer starting work and using {ASK_USER_QUESTION_TOOL_NAME} for specific questions.

## Important Notes

- This tool REQUIRES user approval - they must consent to entering plan mode
"""


def get_enter_plan_mode_tool_prompt() -> str:
    """Match TS: USER_TYPE=ant uses a shorter policy; otherwise external default."""
    if os.environ.get("USER_TYPE") == "ant":
        return _ant_prompt()
    return _external_default(include_what_happens=True)
