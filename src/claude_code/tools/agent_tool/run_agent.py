"""
Agent execution.

Run and manage subagent execution.

Migrated from: tools/AgentTool/runAgent.ts (974 lines)
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

from ..base import ToolResult, ToolUseContext
from .builtin_agents import AgentDefinition, get_agent_by_type
from .constants import is_one_shot_agent


@dataclass
class AgentContext:
    """Context for running an agent."""

    agent_id: str
    agent_type: str
    prompt: str
    description: str
    parent_context: ToolUseContext
    definition: AgentDefinition | None = None
    readonly: bool = False
    model: str | None = None

    # Runtime state
    messages: list[dict[str, Any]] = field(default_factory=list)
    is_running: bool = False
    is_cancelled: bool = False

    @property
    def is_one_shot(self) -> bool:
        return is_one_shot_agent(self.agent_type)


@dataclass
class AgentResult:
    """Result from running an agent."""

    agent_id: str
    success: bool
    result: str
    status: str = "completed"
    usage: dict[str, int] = field(default_factory=dict)
    error: str | None = None


def create_agent_id(label: str | None = None) -> str:
    """
    Create a unique agent ID.

    Format: a{label}-{16 hex chars}

    Args:
        label: Optional label to include in ID

    Returns:
        Agent ID string
    """
    hex_part = uuid.uuid4().hex[:16]
    if label:
        return f"a{label}-{hex_part}"
    return f"a{hex_part}"


async def run_agent(
    input: dict[str, Any],
    context: ToolUseContext,
) -> ToolResult:
    """
    Run a subagent.

    Args:
        input: Agent input (prompt, description, subagent_type, etc.)
        context: Parent tool use context

    Returns:
        ToolResult with agent output
    """
    prompt = input.get("prompt", "")
    description = input.get("description", "")
    subagent_type = input.get("subagent_type", "generalPurpose")
    readonly = input.get("readonly", False)
    resume_id = input.get("resume")
    model = input.get("model")

    # Validate required fields
    if not prompt:
        return ToolResult(
            success=False,
            error="prompt is required",
            error_code=1,
        )

    if not description:
        return ToolResult(
            success=False,
            error="description is required",
            error_code=1,
        )

    # Get or create agent ID
    agent_id = resume_id or create_agent_id(subagent_type)

    # Look up agent definition
    definition = get_agent_by_type(subagent_type)
    if definition is None:
        # Use a default definition for unknown types
        definition = AgentDefinition(
            agent_type=subagent_type,
            name=subagent_type,
            description=description,
            source="user",
        )

    # Override readonly if specified
    if readonly:
        definition.readonly = True

    # Create agent context
    agent_context = AgentContext(
        agent_id=agent_id,
        agent_type=subagent_type,
        prompt=prompt,
        description=description,
        parent_context=context,
        definition=definition,
        readonly=definition.readonly,
        model=model or definition.model,
    )

    # Execute the agent
    try:
        result = await execute_agent(agent_context)

        return ToolResult(
            success=result.success,
            output={
                "agent_id": result.agent_id,
                "result": result.result,
                "status": result.status,
            },
            error=result.error,
        )

    except asyncio.CancelledError:
        return ToolResult(
            success=False,
            output={
                "agent_id": agent_id,
                "result": "",
                "status": "cancelled",
            },
            error="Agent was cancelled",
        )

    except Exception as e:
        return ToolResult(
            success=False,
            output={
                "agent_id": agent_id,
                "result": "",
                "status": "error",
            },
            error=str(e),
        )


async def execute_agent(agent_ctx: AgentContext) -> AgentResult:
    """
    Execute an agent.

    This is where the actual agent execution happens.

    Args:
        agent_ctx: Agent context

    Returns:
        AgentResult
    """
    agent_ctx.is_running = True

    try:
        # Build system prompt
        build_agent_system_prompt(agent_ctx)

        # Create initial user message
        user_message = {
            "role": "user",
            "content": agent_ctx.prompt,
        }
        agent_ctx.messages.append(user_message)

        # In a full implementation, this would:
        # 1. Call the API with the agent's context
        # 2. Process tool calls
        # 3. Continue until completion or cancellation

        # For now, return a stub result
        return AgentResult(
            agent_id=agent_ctx.agent_id,
            success=False,
            result="Agent execution not fully implemented",
            status="error",
            error="Subagent execution requires full query engine integration",
        )

    finally:
        agent_ctx.is_running = False


def build_agent_system_prompt(agent_ctx: AgentContext) -> str:
    """
    Build the system prompt for an agent.

    Args:
        agent_ctx: Agent context

    Returns:
        System prompt string
    """
    definition = agent_ctx.definition

    base_prompt = ""
    if definition and definition.system_prompt:
        base_prompt = definition.system_prompt
    else:
        base_prompt = f"You are a {agent_ctx.agent_type} agent helping with: {agent_ctx.description}"

    # Add readonly notice if applicable
    if agent_ctx.readonly:
        base_prompt += "\n\nNote: You are running in read-only mode. File modifications are not allowed."

    return base_prompt


async def resume_agent(
    agent_id: str,
    context: ToolUseContext,
) -> ToolResult:
    """
    Resume a previously running agent.

    Args:
        agent_id: The agent ID to resume
        context: Parent tool use context

    Returns:
        ToolResult with agent output
    """
    # In a full implementation, this would:
    # 1. Load the agent's saved state
    # 2. Restore the conversation history
    # 3. Continue execution

    return ToolResult(
        success=False,
        output={
            "agent_id": agent_id,
            "result": "",
            "status": "error",
        },
        error="Agent resume not implemented",
    )


def cancel_agent(agent_id: str) -> bool:
    """
    Cancel a running agent.

    Args:
        agent_id: The agent ID to cancel

    Returns:
        True if cancellation was successful
    """
    # In a full implementation, this would signal the agent to stop
    return False
