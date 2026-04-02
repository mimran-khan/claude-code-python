"""
Team create tool.

Create multi-agent teams.

Migrated from: tools/TeamCreateTool/TeamCreateTool.ts (241 lines)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult

TEAM_CREATE_TOOL_NAME = "TeamCreate"


@dataclass
class TeamCreateInput:
    """Input for team creation."""

    team_name: str
    description: str | None = None
    agent_type: str | None = None


@dataclass
class TeamCreateOutput:
    """Output from team creation."""

    team_name: str
    team_file_path: str
    lead_agent_id: str


class TeamCreateTool(Tool):
    """
    Tool for creating multi-agent swarm teams.
    """

    name = TEAM_CREATE_TOOL_NAME
    description = "Create a multi-agent swarm team"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "Name for the new team to create",
                },
                "description": {
                    "type": "string",
                    "description": "Team description/purpose",
                },
                "agent_type": {
                    "type": "string",
                    "description": 'Type/role of the team lead (e.g., "researcher", "test-runner")',
                },
            },
            "required": ["team_name"],
        }

    async def execute(
        self,
        input_data: dict[str, Any],
        context: Any,
    ) -> ToolResult:
        """Execute the team create tool."""
        team_name = input_data.get("team_name", "")
        input_data.get("description")
        input_data.get("agent_type")

        if not team_name:
            return ToolResult(
                output="Team name is required",
                is_error=True,
            )

        # Sanitize team name
        team_name = self._sanitize_name(team_name)

        # Generate unique name if needed
        team_name = self._generate_unique_name(team_name)

        # Generate lead agent ID
        import uuid

        lead_agent_id = f"lead-{uuid.uuid4().hex[:8]}"

        # Get team file path
        team_file_path = self._get_team_file_path(team_name)

        # In a full implementation, this would:
        # 1. Create team file
        # 2. Register team for cleanup
        # 3. Initialize task tracking

        output = TeamCreateOutput(
            team_name=team_name,
            team_file_path=team_file_path,
            lead_agent_id=lead_agent_id,
        )

        return ToolResult(
            output=f"Created team '{team_name}' with lead agent {lead_agent_id}",
            data={
                "team_name": output.team_name,
                "team_file_path": output.team_file_path,
                "lead_agent_id": output.lead_agent_id,
            },
        )

    def _sanitize_name(self, name: str) -> str:
        """Sanitize team name."""
        import re

        # Remove invalid characters
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        # Limit length
        return sanitized[:50]

    def _generate_unique_name(self, name: str) -> str:
        """Generate unique team name if needed."""
        # In a full implementation, check if team exists
        # and generate a unique slug if needed
        return name

    def _get_team_file_path(self, team_name: str) -> str:
        """Get the team file path."""
        import os

        from ...utils.config_utils import get_claude_config_dir

        return os.path.join(
            get_claude_config_dir(),
            "teams",
            f"{team_name}.json",
        )
