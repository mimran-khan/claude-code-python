"""
Agent tool constants.

Constants for the agent system.

Migrated from: tools/AgentTool/constants.ts
"""

from __future__ import annotations

# Tool names
AGENT_TOOL_NAME = "Agent"
LEGACY_AGENT_TOOL_NAME = "Task"

# Special agent types
VERIFICATION_AGENT_TYPE = "verification"

# One-shot agents that don't need continuation
ONE_SHOT_BUILTIN_AGENT_TYPES: frozenset[str] = frozenset(
    [
        "Explore",
        "Plan",
    ]
)


def is_one_shot_agent(agent_type: str) -> bool:
    """Check if an agent type is one-shot (no continuation needed)."""
    return agent_type in ONE_SHOT_BUILTIN_AGENT_TYPES
