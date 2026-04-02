"""
Magic Docs implementation.

Migrated from: services/MagicDocs/magicDocs.ts
"""

import re
from dataclasses import dataclass

# Magic Doc header pattern: # MAGIC DOC: [title]
MAGIC_DOC_HEADER_PATTERN = re.compile(r"^#\s*MAGIC\s+DOC:\s*(.+)$", re.IGNORECASE | re.MULTILINE)

# Pattern to match italics on the line immediately after the header
ITALICS_PATTERN = re.compile(r"^[_*](.+?)[_*]\s*$", re.MULTILINE)


@dataclass
class MagicDocInfo:
    """Information about a tracked magic doc."""

    path: str


@dataclass
class MagicDocHeader:
    """Parsed magic doc header."""

    title: str
    instructions: str | None = None


# Track magic docs
_tracked_magic_docs: dict[str, MagicDocInfo] = {}


def clear_tracked_magic_docs() -> None:
    """Clear all tracked magic docs."""
    _tracked_magic_docs.clear()


def get_tracked_magic_docs() -> dict[str, MagicDocInfo]:
    """Get all tracked magic docs."""
    return dict(_tracked_magic_docs)


def detect_magic_doc_header(content: str) -> MagicDocHeader | None:
    """Detect if a file content contains a Magic Doc header.

    Returns an object with title and optional instructions, or None if not a magic doc.

    Args:
        content: File content to check

    Returns:
        MagicDocHeader if found, None otherwise
    """
    match = MAGIC_DOC_HEADER_PATTERN.search(content)
    if not match or not match.group(1):
        return None

    title = match.group(1).strip()

    # Look for italics on the next line after the header
    header_end_index = match.end()
    after_header = content[header_end_index:]

    # Match: newline, optional blank line, then content line
    next_line_match = re.match(r"^\s*\n(?:\s*\n)?(.+?)(?:\n|$)", after_header)

    if next_line_match and next_line_match.group(1):
        next_line = next_line_match.group(1)
        italics_match = ITALICS_PATTERN.match(next_line)
        if italics_match and italics_match.group(1):
            instructions = italics_match.group(1).strip()
            return MagicDocHeader(title=title, instructions=instructions)

    return MagicDocHeader(title=title)


def register_magic_doc(file_path: str) -> None:
    """Register a file as a Magic Doc when it's read.

    Only registers once per file path.
    """
    if file_path not in _tracked_magic_docs:
        _tracked_magic_docs[file_path] = MagicDocInfo(path=file_path)


def unregister_magic_doc(file_path: str) -> None:
    """Unregister a magic doc."""
    _tracked_magic_docs.pop(file_path, None)


def is_magic_doc(file_path: str) -> bool:
    """Check if a file is registered as a magic doc."""
    return file_path in _tracked_magic_docs


def is_magic_doc_content(content: str) -> bool:
    """Check if content is a magic doc."""
    return detect_magic_doc_header(content) is not None
