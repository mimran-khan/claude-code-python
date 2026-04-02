"""
Directory completion suggestions.

Migrated from: utils/suggestions/directoryCompletion.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DirectorySuggestion:
    """A directory suggestion."""

    path: str
    name: str
    is_directory: bool = True
    is_hidden: bool = False


def get_directory_suggestions(
    partial_path: str,
    cwd: str | None = None,
    max_results: int = 20,
    include_files: bool = False,
    include_hidden: bool = False,
) -> list[DirectorySuggestion]:
    """
    Get directory suggestions for a partial path.

    Args:
        partial_path: Partial path to complete
        cwd: Current working directory
        max_results: Maximum results
        include_files: Include files in results
        include_hidden: Include hidden files/dirs

    Returns:
        List of suggestions
    """
    if cwd is None:
        cwd = os.getcwd()

    # Handle ~ expansion
    if partial_path.startswith("~"):
        partial_path = os.path.expanduser(partial_path)

    # Handle relative paths
    if not os.path.isabs(partial_path):
        partial_path = os.path.join(cwd, partial_path)

    # Get directory and prefix
    if partial_path.endswith(os.sep):
        search_dir = partial_path
        prefix = ""
    else:
        search_dir = os.path.dirname(partial_path)
        prefix = os.path.basename(partial_path).lower()

    if not os.path.isdir(search_dir):
        return []

    suggestions: list[DirectorySuggestion] = []

    try:
        entries = os.listdir(search_dir)
    except PermissionError:
        return []

    for entry in sorted(entries):
        # Skip hidden unless requested
        if entry.startswith(".") and not include_hidden and not prefix.startswith("."):
            continue

        # Match prefix
        if prefix and not entry.lower().startswith(prefix):
            continue

        full_path = os.path.join(search_dir, entry)
        is_dir = os.path.isdir(full_path)

        # Skip files unless requested
        if not is_dir and not include_files:
            continue

        suggestions.append(
            DirectorySuggestion(
                path=full_path,
                name=entry,
                is_directory=is_dir,
                is_hidden=entry.startswith("."),
            )
        )

        if len(suggestions) >= max_results:
            break

    return suggestions


def complete_path(
    partial_path: str,
    cwd: str | None = None,
) -> str | None:
    """
    Complete a partial path to a full path.

    Args:
        partial_path: Partial path
        cwd: Current working directory

    Returns:
        Completed path or None
    """
    suggestions = get_directory_suggestions(
        partial_path,
        cwd=cwd,
        max_results=1,
        include_files=True,
    )

    if suggestions:
        return suggestions[0].path

    return None


def get_parent_directories(
    path: str,
    max_depth: int = 5,
) -> list[str]:
    """
    Get parent directories up to max_depth.

    Args:
        path: Starting path
        max_depth: Maximum depth

    Returns:
        List of parent directories
    """
    parents: list[str] = []
    current = Path(path).resolve()

    for _ in range(max_depth):
        parent = current.parent
        if parent == current:
            break
        parents.append(str(parent))
        current = parent

    return parents
