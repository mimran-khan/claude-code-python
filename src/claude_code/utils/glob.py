"""
Glob pattern utilities.

Provides functions for file pattern matching using glob patterns.

Migrated from: utils/glob.ts (131 lines)
"""

from __future__ import annotations

import contextlib
import os
import re
from pathlib import Path

from .platform import get_platform


def extract_glob_base_directory(pattern: str) -> tuple[str, str]:
    """
    Extract the static base directory from a glob pattern.

    The base directory is everything before the first glob special character.

    Args:
        pattern: The glob pattern.

    Returns:
        A tuple of (base_dir, relative_pattern).
    """
    # Find the first glob special character: *, ?, [, {
    match = re.search(r"[*?\[{]", pattern)

    if match is None:
        # No glob characters - this is a literal path
        dir_path = os.path.dirname(pattern)
        file_name = os.path.basename(pattern)
        return (dir_path, file_name)

    # Get everything before the first glob character
    static_prefix = pattern[: match.start()]

    # Find the last path separator in the static prefix
    last_sep_index = max(
        static_prefix.rfind("/"),
        static_prefix.rfind(os.sep),
    )

    if last_sep_index == -1:
        # No path separator before the glob - pattern is relative to cwd
        return ("", pattern)

    base_dir = static_prefix[:last_sep_index]
    relative_pattern = pattern[last_sep_index + 1 :]

    # Handle root directory patterns
    if base_dir == "" and last_sep_index == 0:
        base_dir = "/"

    # Handle Windows drive root paths
    if get_platform() == "windows" and re.match(r"^[A-Za-z]:$", base_dir):
        base_dir = base_dir + os.sep

    return (base_dir, relative_pattern)


async def glob(
    file_pattern: str,
    cwd: str,
    *,
    limit: int,
    offset: int = 0,
    no_ignore: bool = True,
    hidden: bool = True,
) -> tuple[list[str], bool]:
    """
    Search for files matching a glob pattern.

    Args:
        file_pattern: The glob pattern to match.
        cwd: The current working directory.
        limit: Maximum number of results.
        offset: Number of results to skip.
        no_ignore: Whether to ignore .gitignore files.
        hidden: Whether to include hidden files.

    Returns:
        A tuple of (files, truncated) where files is a list of matching
        file paths and truncated indicates if results were limited.
    """

    search_dir = cwd
    search_pattern = file_pattern

    # Handle absolute paths
    if os.path.isabs(file_pattern):
        base_dir, relative_pattern = extract_glob_base_directory(file_pattern)
        if base_dir:
            search_dir = base_dir
            search_pattern = relative_pattern

    # Prepend ** if pattern doesn't start with it for recursive matching
    if not search_pattern.startswith("**"):
        search_pattern = "**/" + search_pattern

    # Collect matching files
    all_paths: list[str] = []

    try:
        # Use pathlib for glob matching
        path = Path(search_dir)

        for match in path.glob(search_pattern):
            if match.is_file():
                # Skip hidden files if not requested
                if not hidden and any(part.startswith(".") for part in match.parts):
                    continue
                all_paths.append(str(match))
    except Exception:
        pass

    # Sort by modification time (newest first for consistency)
    with contextlib.suppress(Exception):
        all_paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    truncated = len(all_paths) > offset + limit
    files = all_paths[offset : offset + limit]

    return (files, truncated)
