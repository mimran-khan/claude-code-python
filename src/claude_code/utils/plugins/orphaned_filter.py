"""
Ripgrep glob exclusions for orphaned plugin cache versions.

Migrated from: utils/plugins/orphanedPluginFilter.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final

from ..ripgrep import ripgrep
from .plugin_directories import get_plugins_directory

ORPHANED_AT_FILENAME: Final[str] = ".orphaned_at"

_cached_exclusions: list[str] | None = None


@dataclass(frozen=True)
class OrphanExclusionPattern:
    """One ripgrep ``--glob`` exclusion for an orphaned plugin version directory."""

    pattern: str


def _normalize_for_compare(p: str) -> str:
    n = os.path.normpath(p)
    if os.name == "nt":
        return n.lower()
    return n


def paths_overlap(a: str, b: str) -> bool:
    """True if one path is a prefix of the other (mirrors TS pathsOverlap)."""
    na = _normalize_for_compare(a)
    nb = _normalize_for_compare(b)
    sep = os.sep
    return na in (nb, sep) or nb == sep or na.startswith(nb + sep) or nb.startswith(na + sep)


async def get_glob_exclusions_for_plugin_cache(search_path: str | None = None) -> list[str]:
    """
    Return ripgrep --glob exclusion patterns for orphaned version directories.
    """
    global _cached_exclusions
    cache_path = os.path.normpath(os.path.join(get_plugins_directory(), "cache"))

    if search_path and not paths_overlap(search_path, cache_path):
        return []

    if _cached_exclusions is not None:
        return _cached_exclusions

    try:
        markers = await ripgrep(
            [
                "--files",
                "--hidden",
                "--no-ignore",
                "--max-depth",
                "4",
                "--glob",
                ORPHANED_AT_FILENAME,
            ],
            cache_path,
        )
        patterns: list[OrphanExclusionPattern] = []
        for marker_path in markers:
            version_dir = os.path.dirname(marker_path)
            rel = os.path.relpath(version_dir, cache_path) if os.path.isabs(version_dir) else version_dir
            posix_rel = rel.replace("\\", "/")
            patterns.append(OrphanExclusionPattern(f"!**/{posix_rel}/**"))
        _cached_exclusions = [p.pattern for p in patterns]
        return _cached_exclusions
    except Exception:
        _cached_exclusions = []
        return _cached_exclusions


def clear_plugin_cache_exclusions() -> None:
    global _cached_exclusions
    _cached_exclusions = None


__all__ = [
    "OrphanExclusionPattern",
    "clear_plugin_cache_exclusions",
    "get_glob_exclusions_for_plugin_cache",
    "paths_overlap",
]
