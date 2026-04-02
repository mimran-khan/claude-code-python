"""
Token totals for agent description blocks (status notices).

Migrated from: utils/statusNoticeHelpers.ts
"""

from __future__ import annotations

from typing import Any

from ..services.token_estimation import rough_token_count_estimation

AGENT_DESCRIPTIONS_THRESHOLD = 15_000


def get_agent_descriptions_total_tokens(agent_definitions: Any | None) -> int:
    """Sum rough token estimates for non-built-in agent descriptions."""

    if agent_definitions is None:
        return 0

    agents = getattr(agent_definitions, "active_agents", None)
    if agents is None and isinstance(agent_definitions, dict):
        agents = agent_definitions.get("activeAgents")
    if not agents:
        return 0

    total = 0
    for agent in agents:
        if isinstance(agent, dict):
            source = agent.get("source")
            agent_type = agent.get("agentType", "")
            when = agent.get("whenToUse", "")
        else:
            source = getattr(agent, "source", None)
            agent_type = getattr(agent, "agent_type", "") or getattr(agent, "agentType", "")
            when = getattr(agent, "when_to_use", "") or getattr(agent, "whenToUse", "")
        if source == "built-in":
            continue
        description = f"{agent_type}: {when}"
        total += rough_token_count_estimation(description)
    return total


__all__ = ["AGENT_DESCRIPTIONS_THRESHOLD", "get_agent_descriptions_total_tokens"]
