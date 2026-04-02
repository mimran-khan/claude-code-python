"""Disband swarm team and clean up directories."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

TEAM_DELETE_TOOL_NAME = "TeamDelete"
TEAM_LEAD_NAME = "team-lead"


@dataclass
class TeamDeleteOutput:
    success: bool
    message: str
    team_name: str | None = None


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {},
}


class TeamDeleteTool(Tool):
    name = TEAM_DELETE_TOOL_NAME
    description = "Clean up team and task directories when the swarm is complete"
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = False
    user_facing_name = ""

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[TeamDeleteOutput]:
        get_state = context.get_app_state
        set_state = context.set_app_state
        if not get_state or not set_state:
            return ToolResult(
                data=TeamDeleteOutput(
                    success=False,
                    message="App state callbacks are not configured on ToolUseContext.",
                ),
            )

        app = get_state()
        team_ctx = getattr(app, "team_context", None) or (app.get("team_context") if isinstance(app, dict) else None)
        team_name: str | None = None
        if isinstance(team_ctx, dict):
            team_name = team_ctx.get("team_name") or team_ctx.get("teamName")
        elif team_ctx is not None:
            team_name = getattr(team_ctx, "team_name", None) or getattr(team_ctx, "teamName", None)

        cleanup_fn: Callable[[str], Any] | None = None
        if context.options:
            cleanup_fn = context.options.get("team_cleanup_fn")

        if team_name and cleanup_fn:
            team_file = context.options.get("read_team_file_fn") if context.options else None
            if callable(team_file):
                tf = team_file(team_name)
                if tf and isinstance(tf, dict):
                    members = tf.get("members", [])
                    active = [
                        m for m in members if m.get("name") != TEAM_LEAD_NAME and m.get("isActive", True) is not False
                    ]
                    if active:
                        names = ", ".join(str(m.get("name", "")) for m in active)
                        return ToolResult(
                            data=TeamDeleteOutput(
                                success=False,
                                message=(
                                    f"Cannot cleanup team with {len(active)} active member(s): {names}. "
                                    "Terminate teammates first."
                                ),
                                team_name=team_name,
                            ),
                        )
            res = cleanup_fn(team_name)
            if hasattr(res, "__await__"):
                await res

        def _clear(prev: Any) -> Any:
            if isinstance(prev, dict):
                return {**prev, "team_context": None, "inbox": {"messages": []}}
            return prev

        set_state(_clear)

        msg = (
            f'Cleaned up directories and worktrees for team "{team_name}"'
            if team_name
            else "No team name found, nothing to clean up"
        )
        return ToolResult(data=TeamDeleteOutput(success=True, message=msg, team_name=team_name))


def team_delete_prompt() -> str:
    return """
# TeamDelete

Remove team and task directories when the swarm work is complete.

This operation clears team context from the current session. Wire `team_cleanup_fn` and
`read_team_file_fn` via ToolUseContext.options for filesystem cleanup matching the TypeScript app.
""".strip()
