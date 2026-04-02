"""
Skill invocation tool.

Execute skills/commands.

Migrated from: tools/SkillTool/*.ts (3 files)
"""

from .skill_tool import SKILL_TOOL_NAME, SkillTool

__all__ = [
    "SkillTool",
    "SKILL_TOOL_NAME",
]
