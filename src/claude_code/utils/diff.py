"""
Diff utilities.

Provides functions for computing and displaying file diffs.

Migrated from: utils/diff.ts (178 lines)
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from .array import count
from .file import convert_leading_tabs_to_spaces

CONTEXT_LINES = 3
DIFF_TIMEOUT_MS = 5000


@dataclass
class StructuredPatchHunk:
    """A hunk in a structured patch."""

    old_start: int = 0
    old_lines: int = 0
    new_start: int = 0
    new_lines: int = 0
    lines: list[str] = field(default_factory=list)


@dataclass
class FileEdit:
    """An edit to apply to a file."""

    old_string: str
    new_string: str
    replace_all: bool = False


def adjust_hunk_line_numbers(
    hunks: list[StructuredPatchHunk],
    offset: int,
) -> list[StructuredPatchHunk]:
    """
    Shift hunk line numbers by offset.

    Use when getPatchForDisplay received a slice of the file rather than
    the whole file.

    Args:
        hunks: The hunks to adjust.
        offset: The line offset to apply.

    Returns:
        Adjusted hunks with shifted line numbers.
    """
    if offset == 0:
        return hunks

    return [
        StructuredPatchHunk(
            old_start=h.old_start + offset,
            old_lines=h.old_lines,
            new_start=h.new_start + offset,
            new_lines=h.new_lines,
            lines=h.lines,
        )
        for h in hunks
    ]


# Tokens to escape special characters for diff
AMPERSAND_TOKEN = "<<:AMPERSAND_TOKEN:>>"
DOLLAR_TOKEN = "<<:DOLLAR_TOKEN:>>"


def _escape_for_diff(s: str) -> str:
    """Escape special characters for diff processing."""
    return s.replace("&", AMPERSAND_TOKEN).replace("$", DOLLAR_TOKEN)


def _unescape_from_diff(s: str) -> str:
    """Unescape special characters after diff processing."""
    return s.replace(AMPERSAND_TOKEN, "&").replace(DOLLAR_TOKEN, "$")


def count_lines_changed(
    patch: list[StructuredPatchHunk],
    new_file_content: str | None = None,
) -> tuple[int, int]:
    """
    Count lines added and removed in a patch.

    For new files, pass the content string as the second parameter.

    Args:
        patch: Array of diff hunks.
        new_file_content: Optional content string for new files.

    Returns:
        Tuple of (num_additions, num_removals).
    """
    num_additions = 0
    num_removals = 0

    if len(patch) == 0 and new_file_content:
        # For new files, count all lines as additions
        num_additions = len(re.split(r"\r?\n", new_file_content))
    else:
        for hunk in patch:
            num_additions += count(hunk.lines, lambda line: line.startswith("+"))
            num_removals += count(hunk.lines, lambda line: line.startswith("-"))

    return (num_additions, num_removals)


def get_patch_from_contents(
    file_path: str,
    old_content: str,
    new_content: str,
    *,
    ignore_whitespace: bool = False,
    single_hunk: bool = False,
) -> list[StructuredPatchHunk]:
    """
    Get a structured patch from old and new content.

    Args:
        file_path: The file path (for display).
        old_content: The original content.
        new_content: The new content.
        ignore_whitespace: Whether to ignore whitespace differences.
        single_hunk: Whether to return a single hunk.

    Returns:
        List of structured patch hunks.
    """
    context = 100_000 if single_hunk else CONTEXT_LINES

    old_lines = _escape_for_diff(old_content).splitlines(keepends=True)
    new_lines = _escape_for_diff(new_content).splitlines(keepends=True)

    # Generate unified diff
    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=file_path,
            tofile=file_path,
            n=context,
        )
    )

    if not diff:
        return []

    # Parse diff into hunks
    hunks: list[StructuredPatchHunk] = []
    current_hunk: StructuredPatchHunk | None = None

    for line in diff:
        # Parse hunk header
        if line.startswith("@@"):
            if current_hunk:
                hunks.append(current_hunk)

            # Parse @@ -old_start,old_lines +new_start,new_lines @@
            match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                current_hunk = StructuredPatchHunk(
                    old_start=int(match.group(1)),
                    old_lines=int(match.group(2) or "1"),
                    new_start=int(match.group(3)),
                    new_lines=int(match.group(4) or "1"),
                    lines=[],
                )
        elif current_hunk is not None:
            # Skip file headers
            if not line.startswith("---") and not line.startswith("+++"):
                unescaped = _unescape_from_diff(line.rstrip("\n"))
                current_hunk.lines.append(unescaped)

    if current_hunk:
        hunks.append(current_hunk)

    return hunks


def get_patch_for_display(
    file_path: str,
    file_contents: str,
    edits: list[FileEdit],
    *,
    ignore_whitespace: bool = False,
) -> list[StructuredPatchHunk]:
    """
    Get a patch for display with edits applied.

    This function will return the diff with all leading tabs
    rendered as spaces for display.

    Args:
        file_path: The path to the file.
        file_contents: The contents of the file.
        edits: An array of edits to apply to the file.
        ignore_whitespace: Whether to ignore whitespace changes.

    Returns:
        An array of hunks representing the diff.
    """
    prepared = _escape_for_diff(convert_leading_tabs_to_spaces(file_contents))

    # Apply edits
    result = prepared
    for edit in edits:
        escaped_old = _escape_for_diff(convert_leading_tabs_to_spaces(edit.old_string))
        escaped_new = _escape_for_diff(convert_leading_tabs_to_spaces(edit.new_string))

        if edit.replace_all:
            result = result.replace(escaped_old, escaped_new)
        else:
            result = result.replace(escaped_old, escaped_new, 1)

    return get_patch_from_contents(
        file_path,
        _unescape_from_diff(prepared),
        _unescape_from_diff(result),
        ignore_whitespace=ignore_whitespace,
    )
