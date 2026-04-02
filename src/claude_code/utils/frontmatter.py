"""
Frontmatter Parser.

Extracts and parses YAML frontmatter from markdown files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FrontmatterData:
    """Parsed frontmatter data from a markdown file."""

    allowed_tools: list[str] | str | None = None
    description: str | None = None
    type: str | None = None
    argument_hint: str | None = None
    when_to_use: str | None = None
    version: str | None = None
    hide_from_slash_command_tool: str | None = None
    model: str | None = None
    skills: str | None = None
    user_invocable: str | None = None
    hooks: dict[str, Any] | None = None
    effort: str | None = None
    context: str | None = None  # 'inline' or 'fork'
    agent: str | None = None
    paths: list[str] | str | None = None
    shell: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedMarkdown:
    """Result of parsing a markdown file with frontmatter."""

    frontmatter: FrontmatterData
    content: str


# Characters that require quoting in YAML values
YAML_SPECIAL_CHARS = re.compile(r"[{}[\]*&#!|>%@`]|: ")


def quote_problematic_values(frontmatter_text: str) -> str:
    """Pre-process frontmatter to quote values with special YAML characters.

    This allows glob patterns like **/*.{ts,tsx} to be parsed correctly.

    Args:
        frontmatter_text: The raw frontmatter text

    Returns:
        The frontmatter text with problematic values quoted
    """
    lines = frontmatter_text.split("\n")
    result = []

    for line in lines:
        # Match simple key: value lines
        match = re.match(r"^([a-zA-Z_-]+):\s+(.+)$", line)
        if match:
            key, value = match.groups()

            # Skip if already quoted
            if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
                result.append(line)
                continue

            # Quote if contains special characters
            if YAML_SPECIAL_CHARS.search(value):
                # Escape existing single quotes
                escaped = value.replace("'", "''")
                result.append(f"{key}: '{escaped}'")
                continue

        result.append(line)

    return "\n".join(result)


def parse_frontmatter(content: str) -> ParsedMarkdown:
    """Parse frontmatter from markdown content.

    Args:
        content: The full markdown content

    Returns:
        The parsed markdown with frontmatter and content separated
    """
    # Check for frontmatter delimiter
    if not content.startswith("---"):
        return ParsedMarkdown(
            frontmatter=FrontmatterData(),
            content=content,
        )

    # Find the closing delimiter
    lines = content.split("\n")
    end_index = -1

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index == -1:
        return ParsedMarkdown(
            frontmatter=FrontmatterData(),
            content=content,
        )

    # Extract frontmatter text
    frontmatter_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])

    # Quote problematic values before parsing
    frontmatter_text = quote_problematic_values(frontmatter_text)

    # Parse YAML
    try:
        import yaml

        data = yaml.safe_load(frontmatter_text) or {}
    except Exception:
        data = {}

    # Create FrontmatterData
    frontmatter = FrontmatterData(
        allowed_tools=data.get("allowed-tools"),
        description=data.get("description"),
        type=data.get("type"),
        argument_hint=data.get("argument-hint"),
        when_to_use=data.get("when_to_use"),
        version=data.get("version"),
        hide_from_slash_command_tool=data.get("hide-from-slash-command-tool"),
        model=data.get("model"),
        skills=data.get("skills"),
        user_invocable=data.get("user-invocable"),
        hooks=data.get("hooks"),
        effort=data.get("effort"),
        context=data.get("context"),
        agent=data.get("agent"),
        paths=data.get("paths"),
        shell=data.get("shell"),
    )

    # Store extra fields
    known_keys = {
        "allowed-tools",
        "description",
        "type",
        "argument-hint",
        "when_to_use",
        "version",
        "hide-from-slash-command-tool",
        "model",
        "skills",
        "user-invocable",
        "hooks",
        "effort",
        "context",
        "agent",
        "paths",
        "shell",
    }
    for key, value in data.items():
        if key not in known_keys:
            frontmatter.extra[key] = value

    return ParsedMarkdown(
        frontmatter=frontmatter,
        content=body.strip(),
    )


def coerce_description_to_string(description: Any) -> str:
    """Coerce a description value to a string.

    Args:
        description: The description value (may be string, list, or None)

    Returns:
        The description as a string
    """
    if description is None:
        return ""
    if isinstance(description, str):
        return description
    if isinstance(description, list):
        return " ".join(str(item) for item in description)
    return str(description)


def parse_boolean_frontmatter(value: str | None) -> bool | None:
    """Parse a boolean-like frontmatter value.

    Args:
        value: The string value

    Returns:
        The parsed boolean, or None if not a boolean value
    """
    if value is None:
        return None

    value_lower = value.lower()
    if value_lower in ("true", "yes", "1"):
        return True
    if value_lower in ("false", "no", "0"):
        return False

    return None


def split_path_in_frontmatter(paths: str | list[str] | None) -> list[str]:
    """Split a paths frontmatter value into a list.

    Args:
        paths: The paths value (string or list)

    Returns:
        List of path patterns
    """
    if paths is None:
        return []

    if isinstance(paths, list):
        return paths

    # Split by comma and strip whitespace
    return [p.strip() for p in paths.split(",") if p.strip()]
