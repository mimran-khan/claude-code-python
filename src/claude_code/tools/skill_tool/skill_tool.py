"""
Skill tool.

Execute skills and slash commands.

Migrated from: tools/SkillTool/SkillTool.ts (1109 lines)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult

SKILL_TOOL_NAME = "Skill"


@dataclass
class SkillInput:
    """Input for skill execution."""

    skill_name: str
    arguments: str | None = None
    model: str | None = None


class SkillTool(Tool):
    """
    Tool for executing skills and slash commands.

    Skills are markdown-based prompts that can be invoked
    to perform specific tasks.
    """

    name = SKILL_TOOL_NAME
    description = "Execute a skill or slash command"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Name of the skill to execute",
                },
                "arguments": {
                    "type": "string",
                    "description": "Arguments to pass to the skill",
                },
                "model": {
                    "type": "string",
                    "description": "Optional model override for skill execution",
                },
            },
            "required": ["skill_name"],
        }

    async def execute(
        self,
        input_data: dict[str, Any],
        context: Any,
    ) -> ToolResult:
        """Execute the skill tool."""
        skill_name = input_data.get("skill_name", "")
        arguments = input_data.get("arguments")
        model = input_data.get("model")

        if not skill_name:
            return ToolResult(
                output="Skill name is required",
                is_error=True,
            )

        # Look up skill
        skill = self._find_skill(skill_name)

        if skill is None:
            return ToolResult(
                output=f"Skill not found: {skill_name}",
                is_error=True,
            )

        # Execute skill
        try:
            result = await self._execute_skill(skill, arguments, model, context)
            return ToolResult(
                output=result,
            )
        except Exception as e:
            return ToolResult(
                output=f"Skill execution failed: {e}",
                is_error=True,
            )

    def _find_skill(self, name: str) -> dict[str, Any] | None:
        """Find a skill by name."""
        from ...skills import get_all_skills

        skills = get_all_skills()

        for skill in skills:
            if skill.name == name:
                return {
                    "name": skill.name,
                    "content": skill.content,
                    "frontmatter": skill.frontmatter,
                }

            # Check aliases
            if skill.frontmatter.aliases and name in skill.frontmatter.aliases:
                return {
                    "name": skill.name,
                    "content": skill.content,
                    "frontmatter": skill.frontmatter,
                }

        return None

    async def _execute_skill(
        self,
        skill: dict[str, Any],
        arguments: str | None,
        model: str | None,
        context: Any,
    ) -> str:
        """Execute a skill."""
        content = skill.get("content", "")

        # Substitute arguments
        if arguments and "$ARGUMENTS" in content:
            content = content.replace("$ARGUMENTS", arguments)

        # In a full implementation, this would:
        # 1. Parse the skill content
        # 2. Execute shell commands if present
        # 3. Run through the agent loop if needed
        # 4. Return the result

        # For now, return the skill content with substitutions
        return f"[Skill: {skill.get('name')}]\n{content}"

    def validate_input(self, input_data: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate input before execution."""
        skill_name = input_data.get("skill_name")

        if not skill_name:
            return False, "skill_name is required"

        if not isinstance(skill_name, str):
            return False, "skill_name must be a string"

        return True, None
