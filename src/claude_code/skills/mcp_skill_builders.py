"""
Registry for MCP-driven skill construction hooks.

``load_skills_dir`` registers callables so MCP layers can build skills consistently.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

CreateSkillCommandFn = Callable[..., Any]
ParseFrontmatterFn = Callable[..., Any]


@dataclass
class MCPSkillBuilders:
    """Callables used when synthesizing skills from MCP metadata."""

    create_skill_command: CreateSkillCommandFn
    parse_skill_frontmatter_fields: ParseFrontmatterFn


_builders: MCPSkillBuilders | None = None


def register_mcp_skill_builders(builders: MCPSkillBuilders) -> None:
    """Called once from ``load_skills_dir`` after function definitions exist."""
    global _builders
    _builders = builders


def get_mcp_skill_builders() -> MCPSkillBuilders:
    """
    Return registered builders.

    Raises if ``load_skills_dir`` has not been imported yet (mirrors TS
    ``getMCPSkillBuilders``).
    """
    if _builders is None:
        msg = "MCP skill builders not registered — load_skills_dir has not been evaluated yet"
        raise RuntimeError(msg)
    return _builders
