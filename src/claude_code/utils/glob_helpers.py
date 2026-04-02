"""
Glob pattern helpers for file discovery.

Migrated from: utils/globHelpers.ts (source not present; behavior aligned with glob tooling).
"""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GlobOptions:
    """Options for recursive glob matching."""

    cwd: str
    include_hidden: bool = False


def normalize_glob_pattern(pattern: str) -> str:
    """Normalize backslashes to forward slashes for consistent matching."""
    return pattern.replace("\\", "/")


def pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """
    Convert a simple glob (*, ?) to a regex anchored to the full path segment string.

    Does not implement full gitignore semantics; use for coarse filtering.
    """
    norm = normalize_glob_pattern(pattern)
    parts: list[str] = []
    i = 0
    while i < len(norm):
        c = norm[i]
        if c == "*":
            parts.append(".*")
        elif c == "?":
            parts.append(".")
        elif c in ".^$+{}[]|()\\":
            parts.append(re.escape(c))
        else:
            parts.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(parts) + "$", re.IGNORECASE)


def matches_glob(path: str, pattern: str) -> bool:
    """Return True if *path* matches *pattern* using fnmatch (POSIX-style globs)."""
    return fnmatch.fnmatchcase(os.path.normpath(path), normalize_glob_pattern(pattern))


def list_matching_files(root: str, pattern: str, *, options: GlobOptions | None = None) -> list[str]:
    """
    Walk *root* recursively and return files whose relative path matches *pattern*.
    """
    opts = options or GlobOptions(cwd=root)
    matches: list[str] = []
    root_abs = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root_abs):
        # Optionally skip hidden directories
        if not opts.include_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if not opts.include_hidden and name.startswith("."):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, opts.cwd)
            if matches_glob(rel, pattern) or matches_glob(full, pattern):
                matches.append(full)
    return matches
