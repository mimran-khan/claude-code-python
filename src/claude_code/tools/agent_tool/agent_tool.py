"""
Agent Tool implementation (core.tool surface).

Migrated from: tools/AgentTool/AgentTool.tsx, runAgent.ts (orchestration TODO in run_agent).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from ..base import ToolResult as LegacyToolResult
from ..base import ToolUseContext as LegacyToolUseContext
from .builtin_agents import get_builtin_agents
from .constants import AGENT_TOOL_NAME
from .run_agent import run_agent


@dataclass
class AgentInput:
    """Parsed Agent tool input (TS AgentTool / Task schema)."""

    prompt: str
    description: str
    subagent_type: str | None = None
    readonly: bool = False
    resume: str | None = None
    model: str | None = None


@dataclass
class AgentOutput:
    """Agent tool output payload."""

    agent_id: str
    result: str
    status: str


def _core_context_to_legacy(ctx: ToolUseContext) -> LegacyToolUseContext:
    cache: dict[str, Any] = {}
    rfs = ctx.read_file_state
    if hasattr(rfs, "cache"):
        cache = dict(getattr(rfs, "cache", {}) or {})
    return LegacyToolUseContext(
        tool_use_id=(ctx.tool_use_id or ""),
        read_file_state=cache,
        get_app_state=ctx.get_app_state,
        abort_signal=ctx.abort_controller,
    )


def _legacy_result_to_core(tr: LegacyToolResult) -> ToolResult[AgentOutput]:
    out = tr.output if isinstance(tr.output, dict) else {}
    agent_id = str(out.get("agent_id", ""))
    result = str(out.get("result", ""))
    status = str(out.get("status", "completed"))
    if tr.success:
        return ToolResult(data=AgentOutput(agent_id=agent_id, result=result, status=status))
    return ToolResult(
        data=AgentOutput(
            agent_id=agent_id,
            result=result or (tr.error or ""),
            status="error",
        ),
    )


def _build_description() -> str:
    agents = get_builtin_agents()
    lines = "\n".join(f"- {a.agent_type}: {a.description}" for a in agents)
    return (
        "Launch a new agent to handle complex, multi-step tasks autonomously.\n\n"
        "When exploring broadly, prefer an explore-type agent over raw shell search.\n\n"
        f"Available subagent types:\n{lines}"
    )


def _input_schema() -> dict[str, Any]:
    agents = get_builtin_agents()
    agent_types = [a.agent_type for a in agents]
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "prompt": {"type": "string", "description": "The task for the agent to perform"},
            "description": {
                "type": "string",
                "description": "Short (3-5 word) description of the task",
            },
            "subagent_type": {
                "type": "string",
                "description": "Subagent type to use",
                "enum": agent_types,
            },
            "readonly": {
                "type": "boolean",
                "description": "If true, the subagent runs in read-only mode",
            },
            "resume": {"type": "string", "description": "Optional agent ID to resume"},
            "model": {"type": "string", "description": "Optional model override"},
        },
        "required": ["prompt", "description"],
    }


class AgentTool(Tool):
    """Spawn and manage subagents (TS Task / Agent tool)."""

    name = AGENT_TOOL_NAME
    description = _build_description()
    input_schema = _input_schema()
    is_read_only = False
    is_concurrency_safe = True
    user_facing_name = AGENT_TOOL_NAME

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[AgentOutput]:
        _ = progress_callback
        legacy_ctx = _core_context_to_legacy(context)
        legacy_res = await run_agent(input_data, legacy_ctx)
        return _legacy_result_to_core(legacy_res)

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        desc = input_data.get("description")
        if isinstance(desc, str) and desc.strip():
            return desc
        return self.name
