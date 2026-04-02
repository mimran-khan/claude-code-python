"""
Team create tool (base.Tool).

Migrated from: tools/TeamCreateTool/TeamCreateTool.ts
"""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import TEAM_CREATE_TOOL_NAME
from .team_create_prompt import get_team_create_prompt


@dataclass
class TeamCreateToolOutput:
    team_name: str
    team_file_path: str
    lead_agent_id: str


class TeamCreateToolDef(Tool[dict[str, Any], dict[str, Any]]):
    """Create a multi-agent swarm team (simplified local file registration)."""

    @property
    def name(self) -> str:
        return TEAM_CREATE_TOOL_NAME

    @property
    def search_hint(self) -> str | None:
        return "create a multi-agent swarm team"

    async def description(self) -> str:
        return "Create a multi-agent swarm team."

    async def prompt(self) -> str:
        return get_team_create_prompt()

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "team_name": {"type": "string", "description": "Name for the new team to create."},
                "description": {"type": "string", "description": "Team description/purpose."},
                "agent_type": {
                    "type": "string",
                    "description": "Type/role of the team lead (e.g., researcher, test-runner).",
                },
            },
            "required": ["team_name"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "team_name": {"type": "string"},
                "team_file_path": {"type": "string"},
                "lead_agent_id": {"type": "string"},
            },
            "required": ["team_name", "team_file_path", "lead_agent_id"],
        }

    def user_facing_name(self, input: dict[str, Any] | None = None) -> str:
        return ""

    @staticmethod
    def _sanitize_name(name: str) -> str:
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        return sanitized[:50]

    @staticmethod
    def _team_file_path(team_name: str) -> str:
        import os

        try:
            from ...utils.config_utils import get_claude_config_dir
        except ImportError:
            return os.path.join(os.path.expanduser("~"), ".claude", "teams", f"{team_name}.json")
        return os.path.join(get_claude_config_dir(), "teams", f"{team_name}.json")

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = context
        team_name = str(input.get("team_name", "")).strip()
        if not team_name:
            return ToolResult(success=False, error="team_name is required for TeamCreate")

        team_name = self._sanitize_name(team_name)
        lead_agent_id = f"lead-{uuid.uuid4().hex[:8]}"
        team_file_path = self._team_file_path(team_name)

        out = TeamCreateToolOutput(
            team_name=team_name,
            team_file_path=team_file_path,
            lead_agent_id=lead_agent_id,
        )
        return ToolResult(success=True, output=asdict(out))
