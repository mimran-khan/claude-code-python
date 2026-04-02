"""
Skills loader.

Load skills from directories.

Migrated from: skills/loadSkillsDir.ts (1087 lines)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

from ..utils.config_utils import get_claude_config_dir
from ..utils.debug import log_for_debugging

SkillSource = Literal[
    "commands_DEPRECATED",
    "skills",
    "plugin",
    "managed",
    "bundled",
    "mcp",
]


@dataclass
class SkillFrontmatter:
    """Parsed frontmatter from a skill file."""

    name: str | None = None
    description: str | None = None
    aliases: list[str] = field(default_factory=list)
    model: str | None = None
    effort: str | None = None
    tools: list[str] = field(default_factory=list)
    shell: str | None = None
    arguments: list[str] = field(default_factory=list)


@dataclass
class Skill:
    """A loaded skill."""

    name: str
    path: str
    content: str
    source: SkillSource
    frontmatter: SkillFrontmatter = field(default_factory=SkillFrontmatter)
    is_hidden: bool = False
    token_estimate: int = 0


def get_skills_path(
    source: str = "skills",
    base_dir: str | None = None,
) -> str:
    """
    Get the path to skills directory.

    Args:
        source: Source type (skills, plugin, managed)
        base_dir: Base directory override

    Returns:
        Path to skills directory
    """
    if base_dir is None:
        base_dir = get_claude_config_dir()

    if source == "plugin":
        return os.path.join(base_dir, "plugins", "skills")

    if source == "managed":
        return os.path.join(base_dir, "managed", "skills")

    return os.path.join(base_dir, "skills")


def load_skills_dir(
    directory: str,
    source: SkillSource = "skills",
) -> list[Skill]:
    """
    Load skills from a directory.

    Args:
        directory: Directory to load from
        source: Source type

    Returns:
        List of loaded skills
    """
    skills: list[Skill] = []

    if not os.path.isdir(directory):
        return skills

    try:
        for entry in os.listdir(directory):
            path = os.path.join(directory, entry)

            # Skip directories for now (could be nested skills)
            if os.path.isdir(path):
                # Check for SKILL.md in subdirectory
                skill_md = os.path.join(path, "SKILL.md")
                if os.path.exists(skill_md):
                    skill = _load_skill_file(skill_md, source)
                    if skill:
                        skills.append(skill)
                continue

            # Load .md files
            if entry.endswith(".md"):
                skill = _load_skill_file(path, source)
                if skill:
                    skills.append(skill)

    except (OSError, PermissionError) as e:
        log_for_debugging(f"skills: error loading {directory}: {e}")

    return skills


def _load_skill_file(path: str, source: SkillSource) -> Skill | None:
    """Load a single skill file."""
    try:
        with open(path) as f:
            content = f.read()

        # Parse frontmatter
        frontmatter, body = _parse_frontmatter(content)

        # Get name from frontmatter or filename
        name = frontmatter.name
        if not name:
            name = os.path.splitext(os.path.basename(path))[0]
            if name == "SKILL":
                name = os.path.basename(os.path.dirname(path))

        return Skill(
            name=name,
            path=path,
            content=body,
            source=source,
            frontmatter=frontmatter,
            token_estimate=len(body) // 4,  # Rough estimate
        )

    except (OSError, UnicodeDecodeError):
        return None


def _parse_frontmatter(content: str) -> tuple[SkillFrontmatter, str]:
    """Parse YAML frontmatter from content."""
    frontmatter = SkillFrontmatter()
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            import yaml

            try:
                data = yaml.safe_load(parts[1])
                if isinstance(data, dict):
                    frontmatter.name = data.get("name")
                    frontmatter.description = data.get("description")
                    frontmatter.aliases = data.get("aliases", [])
                    frontmatter.model = data.get("model")
                    frontmatter.effort = data.get("effort")
                    frontmatter.tools = data.get("tools", [])
                    frontmatter.shell = data.get("shell")
                    frontmatter.arguments = data.get("arguments", [])
                body = parts[2].strip()
            except yaml.YAMLError:
                pass

    return frontmatter, body


def get_all_skills(
    include_bundled: bool = True,
    include_managed: bool = True,
) -> list[Skill]:
    """
    Get all available skills.

    Args:
        include_bundled: Include bundled skills
        include_managed: Include managed skills

    Returns:
        List of all skills
    """
    skills: list[Skill] = []

    # Load user skills
    user_skills_path = get_skills_path("skills")
    if os.path.isdir(user_skills_path):
        skills.extend(load_skills_dir(user_skills_path, "skills"))

    # Load managed skills
    if include_managed:
        managed_path = get_skills_path("managed")
        if os.path.isdir(managed_path):
            skills.extend(load_skills_dir(managed_path, "managed"))

    # Load bundled skills
    if include_bundled:
        from .bundled import BUNDLED_SKILLS

        skills.extend(BUNDLED_SKILLS)

    return skills
