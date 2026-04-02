"""
Tool-pool resolution and filtering for subagents.

Migrated from: tools/AgentTool/agentToolUtils.ts (minimal port — async task wiring is host-specific).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResolvedAgentTools:
    has_wildcard: bool
    valid_tools: list[str]
    invalid_tools: list[str]
    resolved_tools: dict[str, Any] = field(default_factory=dict)
    allowed_agent_types: list[str] | None = None


def filter_tools_for_agent(
    tools: dict[str, Any],
    *,
    is_builtin: bool,
    is_async: bool = False,
    permission_mode: str | None = None,
) -> dict[str, Any]:
    """
    Apply built-in vs custom disallowed-tool policies.

    Full TS version integrates yolo classifier, teammate context, and constants.
    """
    if is_builtin:
        return dict(tools)
    if permission_mode == "plan" and not is_async:
        return {k: v for k, v in tools.items() if k in ("Read", "Glob", "Grep", "LSP")}
    return dict(tools)


def resolve_agent_tool_names(
    requested: list[str] | None,
    available_is_tool: Callable[[str], bool],
) -> ResolvedAgentTools:
    if requested is None:
        return ResolvedAgentTools(
            has_wildcard=True,
            valid_tools=[],
            invalid_tools=[],
            resolved_tools={},
        )
    valid: list[str] = []
    invalid: list[str] = []
    for name in requested:
        if name == "*":
            return ResolvedAgentTools(
                has_wildcard=True,
                valid_tools=[],
                invalid_tools=[],
                resolved_tools={},
            )
        if available_is_tool(name):
            valid.append(name)
        else:
            invalid.append(name)
    return ResolvedAgentTools(
        has_wildcard=False,
        valid_tools=valid,
        invalid_tools=invalid,
        resolved_tools={},
    )


__all__ = ["ResolvedAgentTools", "filter_tools_for_agent", "resolve_agent_tool_names"]
