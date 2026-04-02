"""
Memory entrypoint handling.

MEMORY.md file management.

Migrated from: memdir/memdir.ts (508 lines)
"""

from __future__ import annotations

from dataclasses import dataclass

ENTRYPOINT_NAME = "MEMORY.md"
MAX_ENTRYPOINT_LINES = 200
MAX_ENTRYPOINT_BYTES = 25_000

# Shared guidance so the model does not burn turns on mkdir/ls before writing.
DIR_EXISTS_GUIDANCE = (
    "This directory already exists — write to it directly with the Write tool "
    "(do not run mkdir or check for its existence)."
)


@dataclass
class EntrypointTruncation:
    """Result of truncating entrypoint content."""

    content: str
    line_count: int
    byte_count: int
    was_line_truncated: bool
    was_byte_truncated: bool


def truncate_entrypoint_content(raw: str) -> EntrypointTruncation:
    """
    Truncate MEMORY.md content to line and byte caps.

    Line-truncates first, then byte-truncates at last newline.

    Args:
        raw: Raw content

    Returns:
        EntrypointTruncation with truncated content
    """
    trimmed = raw.strip()
    content_lines = trimmed.split("\n")
    line_count = len(content_lines)
    byte_count = len(trimmed)

    was_line_truncated = line_count > MAX_ENTRYPOINT_LINES
    was_byte_truncated = byte_count > MAX_ENTRYPOINT_BYTES

    if not was_line_truncated and not was_byte_truncated:
        return EntrypointTruncation(
            content=trimmed,
            line_count=line_count,
            byte_count=byte_count,
            was_line_truncated=False,
            was_byte_truncated=False,
        )

    # Truncate by lines first
    truncated = "\n".join(content_lines[:MAX_ENTRYPOINT_LINES]) if was_line_truncated else trimmed

    # Then truncate by bytes if still too large
    if len(truncated) > MAX_ENTRYPOINT_BYTES:
        # Find last newline before limit
        truncated = truncated[:MAX_ENTRYPOINT_BYTES]
        last_newline = truncated.rfind("\n")
        if last_newline > 0:
            truncated = truncated[:last_newline]

    # Add truncation warning
    warnings: list[str] = []
    if was_line_truncated:
        warnings.append(f"{line_count} lines")
    if was_byte_truncated:
        warnings.append(f"{byte_count:,} bytes")

    if warnings:
        warning = f"\n\n[Truncated: {' and '.join(warnings)} exceeded limit]"
        truncated = truncated + warning

    return EntrypointTruncation(
        content=truncated,
        line_count=line_count,
        byte_count=byte_count,
        was_line_truncated=was_line_truncated,
        was_byte_truncated=was_byte_truncated,
    )


def build_memory_prompt(memory_content: str) -> str:
    """
    Build a prompt section from memory content.

    Args:
        memory_content: Content from MEMORY.md

    Returns:
        Formatted prompt section
    """
    truncation = truncate_entrypoint_content(memory_content)

    return f"""<memory>
{truncation.content}
</memory>"""


def format_memory_size(byte_count: int) -> str:
    """Format memory size for display."""
    from ..utils.format import format_file_size

    return format_file_size(byte_count)
