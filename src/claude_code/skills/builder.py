"""
Skill builder.

Build skills from markdown files.

Migrated from: skills/mcpSkillBuilders.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .loader import Skill, SkillFrontmatter, SkillSource


@dataclass
class SkillBuilder:
    """Builder for creating skills."""

    name: str
    content: str = ""
    description: str = ""
    source: SkillSource = "skills"
    aliases: list[str] | None = None
    tools: list[str] | None = None
    model: str | None = None

    def build(self) -> Skill:
        """Build the skill."""
        frontmatter = SkillFrontmatter(
            name=self.name,
            description=self.description,
            aliases=self.aliases or [],
            model=self.model,
            tools=self.tools or [],
        )

        return Skill(
            name=self.name,
            path=f"builder:{self.name}",
            content=self.content,
            source=self.source,
            frontmatter=frontmatter,
        )


def parse_skill_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content

    Returns:
        Tuple of (frontmatter dict, body content)
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    import yaml

    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        return frontmatter or {}, body
    except yaml.YAMLError:
        return {}, content


def build_skill_from_markdown(
    name: str,
    markdown: str,
    source: SkillSource = "skills",
) -> Skill:
    """
    Build a skill from markdown content.

    Args:
        name: Skill name
        markdown: Markdown content with optional frontmatter
        source: Skill source

    Returns:
        Built Skill
    """
    frontmatter_dict, body = parse_skill_frontmatter(markdown)

    frontmatter = SkillFrontmatter(
        name=frontmatter_dict.get("name", name),
        description=frontmatter_dict.get("description", ""),
        aliases=frontmatter_dict.get("aliases", []),
        model=frontmatter_dict.get("model"),
        effort=frontmatter_dict.get("effort"),
        tools=frontmatter_dict.get("tools", []),
        shell=frontmatter_dict.get("shell"),
        arguments=frontmatter_dict.get("arguments", []),
    )

    return Skill(
        name=frontmatter.name or name,
        path=f"markdown:{name}",
        content=body,
        source=source,
        frontmatter=frontmatter,
        token_estimate=len(body) // 4,
    )


def extract_description_from_markdown(content: str) -> str:
    """
    Extract description from markdown content.

    Uses first paragraph or first heading.

    Args:
        content: Markdown content

    Returns:
        Extracted description
    """
    lines = content.strip().split("\n")

    description_lines: list[str] = []

    for line in lines:
        line = line.strip()

        # Skip headings
        if line.startswith("#"):
            if description_lines:
                break
            continue

        # Skip empty lines at start
        if not line and not description_lines:
            continue

        # End at empty line after content
        if not line and description_lines:
            break

        description_lines.append(line)

    return " ".join(description_lines)[:200]
