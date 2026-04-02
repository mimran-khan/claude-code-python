"""
Agent Tool Implementation.

Launches specialized agents to handle complex tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import AGENT_TOOL_NAME, AgentDefinition, get_prompt


class AgentInput(BaseModel):
    """Input parameters for agent tool."""

    prompt: str = Field(
        ...,
        description="The task for the agent to perform.",
    )
    description: str = Field(
        ...,
        description="A short (3-5 word) description of the task.",
    )
    subagent_type: str | None = Field(
        default=None,
        description="The type of agent to use. If omitted, the general-purpose agent is used.",
    )
    name: str | None = Field(
        default=None,
        description="Optional name for the agent instance.",
    )
    model: str | None = Field(
        default=None,
        description="Optional model to use for this agent.",
    )
    isolation: Literal["none", "worktree", "remote"] | None = Field(
        default=None,
        description="Isolation mode: none (default), worktree (git worktree), or remote.",
    )
    run_in_background: bool = Field(
        default=False,
        description="Whether to run the agent in the background.",
    )
    resume: str | None = Field(
        default=None,
        description="Optional agent ID to resume from a previous execution.",
    )
    readonly: bool = Field(
        default=False,
        description="If true, the agent runs in read-only mode.",
    )


@dataclass
class AgentSuccess:
    """Successful agent result."""

    type: Literal["success"] = "success"
    agent_id: str = ""
    result: str = ""
    output_file: str | None = None
    worktree_path: str | None = None
    branch: str | None = None


@dataclass
class AgentPending:
    """Agent is running in background."""

    type: Literal["pending"] = "pending"
    agent_id: str = ""
    message: str = "Agent is running in background. You will be notified when it completes."


@dataclass
class AgentError:
    """Failed agent result."""

    type: Literal["error"] = "error"
    agent_id: str = ""
    error: str = ""


AgentOutput = AgentSuccess | AgentPending | AgentError


class AgentTool(Tool[AgentInput, AgentOutput]):
    """
    Tool for launching specialized agents.

    Agents are subprocesses that can autonomously handle complex,
    multi-step tasks. Each agent type has specific capabilities
    and tools available to it.
    """

    _agent_definitions: list[AgentDefinition] = []
    _allowed_agent_types: list[str] | None = None

    @property
    def name(self) -> str:
        return AGENT_TOOL_NAME

    @property
    def description(self) -> str:
        # Return a static description - full prompt is async
        return "Launch a new agent to handle complex, multi-step tasks autonomously."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The task for the agent to perform.",
                },
                "description": {
                    "type": "string",
                    "description": "A short (3-5 word) description of the task.",
                },
                "subagent_type": {
                    "type": "string",
                    "description": "The type of agent to use. If omitted, the general-purpose agent is used.",
                },
                "name": {
                    "type": "string",
                    "description": "Optional name for the agent instance.",
                },
                "model": {
                    "type": "string",
                    "description": "Optional model to use for this agent.",
                },
                "isolation": {
                    "type": "string",
                    "enum": ["none", "worktree", "remote"],
                    "description": "Isolation mode: none (default), worktree (git worktree), or remote.",
                },
                "run_in_background": {
                    "type": "boolean",
                    "description": "Whether to run the agent in the background.",
                    "default": False,
                },
                "resume": {
                    "type": "string",
                    "description": "Optional agent ID to resume from a previous execution.",
                },
                "readonly": {
                    "type": "boolean",
                    "description": "If true, the agent runs in read-only mode.",
                    "default": False,
                },
            },
            "required": ["prompt", "description"],
        }

    def is_read_only(self, input_data: AgentInput) -> bool:
        return input_data.readonly

    async def call(
        self,
        input_data: AgentInput,
        context: Any,
    ) -> ToolResult[AgentOutput]:
        """Execute the agent launch operation."""
        # In a full implementation, this would:
        # 1. Validate the agent type
        # 2. Create/resume an agent subprocess
        # 3. Pass the prompt and configuration
        # 4. Return the agent ID and result (or pending status)

        # For now, return a placeholder
        import uuid

        agent_id = str(uuid.uuid4())[:8]

        return ToolResult(
            success=False,
            output=AgentError(
                agent_id=agent_id,
                error=("Agent execution requires full runtime integration. This is a placeholder implementation."),
            ),
        )

    def user_facing_name(self, input_data: AgentInput | None = None) -> str:
        """Get the user-facing name for this tool."""
        if input_data and input_data.subagent_type:
            return input_data.subagent_type
        return "Agent"

    def get_tool_use_summary(self, input_data: AgentInput | None) -> str | None:
        """Get a short summary of this tool use."""
        if input_data and input_data.description:
            return input_data.description
        return None

    def get_activity_description(self, input_data: AgentInput | None) -> str | None:
        """Get a human-readable activity description."""
        if input_data:
            if input_data.name:
                return f"Running {input_data.name}"
            if input_data.subagent_type:
                return f"Running {input_data.subagent_type}"
            if input_data.description:
                return input_data.description
        return "Running agent"

    async def get_full_prompt(self, is_coordinator: bool = False) -> str:
        """Get the full prompt including agent definitions.

        Args:
            is_coordinator: Whether this is coordinator mode

        Returns:
            The full prompt string
        """
        return await get_prompt(
            self._agent_definitions,
            is_coordinator=is_coordinator,
            allowed_agent_types=self._allowed_agent_types,
        )

    def set_agent_definitions(
        self,
        definitions: list[AgentDefinition],
        allowed_types: list[str] | None = None,
    ) -> None:
        """Set the available agent definitions.

        Args:
            definitions: List of agent definitions
            allowed_types: Optional list of allowed agent types
        """
        self._agent_definitions = definitions
        self._allowed_agent_types = allowed_types
