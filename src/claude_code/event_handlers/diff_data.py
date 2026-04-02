"""
Git worktree diff aggregation for UI (stats, per-file flags, hunks map).

Migrated from: hooks/useDiffData.ts
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

MAX_LINES_PER_FILE = 400


@dataclass(frozen=True)
class DiffFile:
    path: str
    lines_added: int
    lines_removed: int
    is_binary: bool
    is_large_file: bool
    is_truncated: bool
    is_new_file: bool | None = None
    is_untracked: bool | None = None


@dataclass
class GitDiffStats:
    """Subset of TS GitDiffStats used by build_diff_data."""

    files_changed: int | None = None
    insertions: int | None = None
    deletions: int | None = None


@dataclass
class GitDiffResult:
    stats: GitDiffStats | None
    per_file_stats: dict[str, Any]


@dataclass
class DiffData:
    stats: GitDiffStats | None
    files: list[DiffFile]
    hunks: dict[str, list[Any]]
    loading: bool


def build_diff_data(
    diff_result: GitDiffResult | None,
    hunks: Mapping[str, list[Any]],
    *,
    loading: bool,
) -> DiffData:
    """
    Pure transform matching ``useDiffData`` memo (excluding async fetch).

    ``per_file_stats`` values must expose ``added``, ``removed``, ``is_binary``,
    and optional ``is_untracked``.
    """
    if diff_result is None:
        return DiffData(stats=None, files=[], hunks=dict(hunks), loading=loading)

    stats = diff_result.stats
    files: list[DiffFile] = []
    for path, file_stats in diff_result.per_file_stats.items():
        fs = file_stats
        if isinstance(fs, dict):
            added = int(fs.get("added", 0))
            removed = int(fs.get("removed", 0))
            is_binary = bool(fs.get("isBinary", fs.get("is_binary", False)))
            is_untracked = fs.get("isUntracked", fs.get("is_untracked"))
        else:
            added = int(getattr(fs, "added", 0))
            removed = int(getattr(fs, "removed", 0))
            is_binary = bool(getattr(fs, "is_binary", False))
            is_untracked = getattr(fs, "is_untracked", None)
        is_untracked_b = bool(is_untracked) if is_untracked is not None else False

        file_hunks = hunks.get(path)
        is_large_file = not is_binary and not is_untracked_b and file_hunks is None
        total_lines = added + removed
        is_truncated = not is_large_file and not is_binary and total_lines > MAX_LINES_PER_FILE
        files.append(
            DiffFile(
                path=path,
                lines_added=added,
                lines_removed=removed,
                is_binary=is_binary,
                is_large_file=is_large_file,
                is_truncated=is_truncated,
                is_untracked=is_untracked if is_untracked is not None else None,
            )
        )

    files.sort(key=lambda f: f.path)
    return DiffData(stats=stats, files=files, hunks=dict(hunks), loading=False)
