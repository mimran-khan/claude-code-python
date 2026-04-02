"""Exit plan mode v2 tool. Migrated from tools/ExitPlanModeTool/ExitPlanModeV2Tool.ts (Python subset)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ...core.tool import (
    Tool,
    ToolCallProgress,
    ToolResult,
    ToolUseContext,
    ValidationResult,
    tool_matches_name,
)
from .constants import EXIT_PLAN_MODE_V2_TOOL_NAME


@dataclass
class AllowedPrompt:
    """Prompt-based permission entry when exiting plan mode."""

    tool: str
    prompt: str


@dataclass
class ExitPlanModeV2Input:
    """Normalized input for ExitPlanMode v2."""

    allowed_prompts: list[AllowedPrompt] = field(default_factory=list)
    plan: str | None = None
    plan_file_path: str | None = None


@dataclass
class ExitPlanModeV2Output:
    """Output from ExitPlanMode v2 (TS outputSchema)."""

    plan: str | None
    is_agent: bool
    file_path: str | None = None
    has_task_tool: bool | None = None
    plan_was_edited: bool | None = None
    awaiting_leader_approval: bool | None = None
    request_id: str | None = None


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
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


def _get_plan_from_options(
    input_data: dict[str, Any],
    get_plan_fn: Callable[..., Any] | None,
    agent_id: str | None,
) -> tuple[str | None, str | None]:
    """Return (plan_text, file_path) from input injection or host callback."""
    plan = input_data.get("plan")
    file_path = input_data.get("plan_file_path")
    if isinstance(plan, str) and plan.strip():
        return plan, file_path if isinstance(file_path, str) else None
    if callable(get_plan_fn):
        try:
            res = get_plan_fn(agent_id)
            if hasattr(res, "__await__"):
                raise TypeError("get_plan_fn must be synchronous; use options['get_plan_async']")
            if isinstance(res, tuple) and len(res) == 2:
                p, fp = res
                return (p if isinstance(p, str) else None), (fp if isinstance(fp, str) else None)
            if isinstance(res, str):
                return res, None
        except Exception:
            return None, None
    return None, file_path if isinstance(file_path, str) else None


class ExitPlanModeV2Tool(Tool):
    """Present plan for approval and exit plan mode (v2)."""

    name = EXIT_PLAN_MODE_V2_TOOL_NAME
    description = "Prompts the user to exit plan mode and start coding"
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = True
    user_facing_name = ""

    def validate_input(self, input_data: dict[str, Any]) -> ValidationResult:
        _ = input_data
        return ValidationResult(result=True)

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[ExitPlanModeV2Output]:
        opts = context.options or {}
        is_teammate = bool(opts.get("is_teammate"))
        plan_mode_required = bool(opts.get("plan_mode_required"))

        if not is_teammate and context.get_app_state:
            state = context.get_app_state()
            mode = getattr(
                getattr(state, "tool_permission_context", None),
                "mode",
                None,
            )
            if mode is None and isinstance(state, dict):
                tpc = state.get("tool_permission_context") or {}
                mode = tpc.get("mode")
            if mode != "plan":
                raise RuntimeError(
                    "You are not in plan mode. This tool is only for exiting plan mode after writing a plan. "
                    "If your plan was already approved, continue with implementation.",
                )

        is_agent = bool(context.agent_id)
        get_plan_fn = opts.get("get_plan_sync")
        get_plan_async = opts.get("get_plan_async")
        plan: str | None = None
        file_path: str | None = None

        if callable(get_plan_async):
            plan, file_path = await get_plan_async(context.agent_id)
        else:
            plan, file_path = _get_plan_from_options(input_data, get_plan_fn, context.agent_id)

        input_plan = input_data.get("plan")
        input_plan_str = input_plan if isinstance(input_plan, str) else None
        if input_plan_str is not None:
            plan = input_plan_str
            fp = input_data.get("plan_file_path")
            if isinstance(fp, str):
                file_path = fp
            write_fn = opts.get("write_plan_file_async")
            if callable(write_fn) and file_path:
                await write_fn(file_path, input_plan_str)

        if is_teammate and plan_mode_required:
            if not plan:
                raise RuntimeError(
                    f"No plan content available (plan file: {file_path}). Write the plan before calling ExitPlanMode."
                )
            request_id = str(opts.get("plan_approval_request_id") or "")
            await_fn = opts.get("send_plan_approval_async")
            if callable(await_fn):
                await await_fn(
                    plan=plan,
                    plan_file_path=file_path,
                    request_id=request_id,
                )
            return ToolResult(
                data=ExitPlanModeV2Output(
                    plan=plan,
                    is_agent=True,
                    file_path=file_path,
                    awaiting_leader_approval=True,
                    request_id=request_id or None,
                ),
            )

        restore_fn = opts.get("restore_permission_mode_after_plan_async")
        if callable(restore_fn):
            await restore_fn(context)

        tools_list = opts.get("tools") or []
        has_task_tool = False
        if isinstance(tools_list, list):
            agent_tool_name = opts.get("agent_tool_name", "Task")
            for t in tools_list:
                if isinstance(t, dict) and tool_matches_name(t, str(agent_tool_name)):
                    has_task_tool = True
                    break

        return ToolResult(
            data=ExitPlanModeV2Output(
                plan=plan,
                is_agent=is_agent,
                file_path=file_path,
                has_task_tool=has_task_tool or None,
                plan_was_edited=(input_plan_str is not None) or None,
            ),
        )
