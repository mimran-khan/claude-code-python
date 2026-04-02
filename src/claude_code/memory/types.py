"""
Memory Types.

Type definitions for the memory system.
Memory types capture context NOT derivable from the current project state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# Memory type taxonomy
MEMORY_TYPES = ("user", "feedback", "project", "reference")

MemoryType = Literal["user", "feedback", "project", "reference"]


def parse_memory_type(raw: str | None) -> MemoryType | None:
    """Parse a raw frontmatter value into a MemoryType.

    Args:
        raw: The raw string value from frontmatter

    Returns:
        The parsed memory type, or None if invalid
    """
    if raw is None or not isinstance(raw, str):
        return None
    if raw in MEMORY_TYPES:
        return raw  # type: ignore
    return None


@dataclass
class MemoryFrontmatter:
    """Frontmatter data for a memory file."""

    name: str = ""
    description: str = ""
    type: MemoryType | None = None
    scope: Literal["private", "team"] | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Memory:
    """A memory record."""

    name: str
    description: str = ""
    content: str = ""
    type: MemoryType | None = None
    scope: Literal["private", "team"] = "private"
    path: str = ""
    frontmatter: MemoryFrontmatter = field(default_factory=MemoryFrontmatter)

    # Metadata
    created_at: str | None = None
    updated_at: str | None = None

    # Flags
    is_stale: bool = False


# What NOT to save in memory
WHAT_NOT_TO_SAVE = [
    "Code patterns, conventions, architecture, file paths, or project structure — these can be derived by reading the current project state.",
    "Git history, recent changes, or who-changed-what — `git log` / `git blame` are authoritative.",
    "Debugging solutions or fix recipes — the fix is in the code; the commit message has the context.",
    "Anything already documented in CLAUDE.md files.",
    "Ephemeral task details: in-progress work, temporary state, current conversation context.",
]


# Memory drift caveat
MEMORY_DRIFT_CAVEAT = (
    "Memory records can become stale over time. Use memory as context for what was "
    "true at a given point in time. Before answering the user or building assumptions "
    "based solely on information in memory records, verify that the memory is still "
    "correct and up-to-date by reading the current state of the files or resources. "
    "If a recalled memory conflicts with current information, trust what you observe "
    "now — and update or remove the stale memory rather than acting on it."
)
