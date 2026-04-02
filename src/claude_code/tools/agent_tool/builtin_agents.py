"""
Built-in agent definitions.

Standard agents available by default.

Migrated from: tools/AgentTool/builtInAgents.ts + built-in/*.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

AgentSource = Literal["builtin", "plugin", "user", "project", "managed"]


@dataclass
class AgentDefinition:
    """Definition of an agent."""

    agent_type: str
    name: str
    description: str
    system_prompt: str = ""
    tools: list[str] = field(default_factory=list)
    model: str | None = None
    readonly: bool = False
    source: AgentSource = "builtin"
    mcp_servers: list[str] = field(default_factory=list)

    @property
    def is_builtin(self) -> bool:
        return self.source == "builtin"


# General Purpose Agent
GENERAL_PURPOSE_AGENT = AgentDefinition(
    agent_type="generalPurpose",
    name="General Purpose",
    description="Research and execute multi-step tasks autonomously",
    system_prompt="""You are a general-purpose coding agent that helps with complex tasks.

Your approach:
1. Understand the full scope of the task
2. Break it down into manageable steps
3. Execute each step carefully
4. Verify your work as you go
5. Report results clearly

You have access to all standard tools for file operations, code search, and shell commands.""",
    tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    source="builtin",
)


# Explore Agent
EXPLORE_AGENT = AgentDefinition(
    agent_type="Explore",
    name="Explore",
    description="Fast codebase exploration and analysis",
    system_prompt="""You are a fast exploration agent specialized in codebase discovery.

Your role:
- Quickly find files matching patterns
- Search for code symbols and patterns
- Map out codebase structure
- Answer questions about code organization

Be efficient and thorough. Use Glob for file patterns, Grep for content search.""",
    tools=["Read", "Glob", "Grep"],
    readonly=True,
    source="builtin",
)


# Plan Agent
PLAN_AGENT = AgentDefinition(
    agent_type="Plan",
    name="Plan",
    description="Design implementation approaches before coding",
    system_prompt="""You are a planning agent that helps design solutions before implementation.

Your role:
- Understand requirements thoroughly
- Explore the codebase to understand existing patterns
- Design a clear implementation plan
- Identify potential issues and trade-offs
- Present options with pros and cons

Focus on clarity and completeness. Your plans guide implementation.""",
    tools=["Read", "Glob", "Grep"],
    readonly=True,
    source="builtin",
)


# Shell Agent
SHELL_AGENT = AgentDefinition(
    agent_type="shell",
    name="Shell",
    description="Command execution specialist",
    system_prompt="""You are a shell command specialist.

Your role:
- Execute bash/shell commands as requested
- Handle git operations
- Run build commands and tests
- Manage system operations

Be careful with destructive operations. Always verify before executing risky commands.""",
    tools=["Bash", "Read"],
    source="builtin",
)


# Verification Agent
VERIFICATION_AGENT = AgentDefinition(
    agent_type="verification",
    name="Verification",
    description="Verify implementations meet requirements",
    system_prompt="""You are a verification agent that ensures implementations are correct.

Your role:
- Review code changes against requirements
- Run tests and verify they pass
- Check for edge cases
- Identify potential issues
- Report verification status

Be thorough and systematic. Quality matters.""",
    tools=["Read", "Bash", "Glob", "Grep"],
    readonly=True,
    source="builtin",
)


def get_builtin_agents() -> list[AgentDefinition]:
    """
    Get all built-in agents.

    Returns:
        List of built-in AgentDefinition objects
    """
    from ...utils.env_utils import is_env_truthy

    # Check if built-in agents are disabled (SDK mode)
    if is_env_truthy(os.getenv("CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS")):
        return []

    agents = [
        GENERAL_PURPOSE_AGENT,
        EXPLORE_AGENT,
        PLAN_AGENT,
        SHELL_AGENT,
    ]

    # Verification agent may be feature-gated
    if is_env_truthy(os.getenv("CLAUDE_CODE_ENABLE_VERIFICATION_AGENT")):
        agents.append(VERIFICATION_AGENT)

    return agents


def get_agent_by_type(agent_type: str) -> AgentDefinition | None:
    """
    Get a built-in agent by type.

    Args:
        agent_type: The agent type to find

    Returns:
        AgentDefinition or None if not found
    """
    for agent in get_builtin_agents():
        if agent.agent_type.lower() == agent_type.lower():
            return agent
    return None


def is_builtin_agent(agent_type: str) -> bool:
    """Check if an agent type is a built-in agent."""
    return get_agent_by_type(agent_type) is not None
