"""
CLI / TUI display helpers for agent listings.

Migrated from: tools/AgentTool/agentDisplay.ts
"""

from __future__ import annotations

from typing import Any, TypedDict, cast

AgentSource = str


class AgentSourceGroup(TypedDict):
    label: str
    source: AgentSource


AGENT_SOURCE_GROUPS: list[AgentSourceGroup] = [
    {"label": "User agents", "source": "userSettings"},
    {"label": "Project agents", "source": "projectSettings"},
    {"label": "Local agents", "source": "localSettings"},
    {"label": "Managed agents", "source": "policySettings"},
    {"label": "Plugin agents", "source": "plugin"},
    {"label": "CLI arg agents", "source": "flagSettings"},
    {"label": "Built-in agents", "source": "built-in"},
]


class ResolvedAgent(TypedDict, total=False):
    agentType: str
    source: AgentSource
    overriddenBy: AgentSource | None


def resolve_agent_overrides(
    all_agents: list[dict[str, Any]],
    active_agents: list[dict[str, Any]],
) -> list[ResolvedAgent]:
    active_map = {a["agentType"]: a for a in active_agents if a.get("agentType")}
    seen: set[str] = set()
    out: list[ResolvedAgent] = []
    for agent in all_agents:
        at = agent.get("agentType")
        src = str(agent.get("source", ""))
        if not isinstance(at, str):
            continue
        key = f"{at}:{src}"
        if key in seen:
            continue
        seen.add(key)
        winner = active_map.get(at)
        overridden_by = None
        if winner and winner.get("source") != agent.get("source"):
            overridden_by = str(winner.get("source"))
        row = dict(agent)
        row["overriddenBy"] = overridden_by
        out.append(cast(ResolvedAgent, row))
    return out


def resolve_agent_model_display(agent: dict[str, Any]) -> str | None:
    m = agent.get("model")
    if m is None:
        return None
    s = str(m).strip()
    return "inherit" if s.lower() == "inherit" else s


__all__ = [
    "AGENT_SOURCE_GROUPS",
    "AgentSourceGroup",
    "ResolvedAgent",
    "resolve_agent_model_display",
    "resolve_agent_overrides",
]
