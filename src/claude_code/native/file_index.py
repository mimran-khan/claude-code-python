"""
File index for fuzzy file searching.

Pure Python port of the Rust NAPI module that wraps nucleo.

Migrated from: native-ts/file-index/index.ts
"""

import asyncio
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Search result with path and score."""

    path: str
    score: float


# Scoring constants (approximating fzf-v2 / nucleo bonuses)
SCORE_MATCH = 16
BONUS_BOUNDARY = 8
BONUS_CAMEL = 6
BONUS_CONSECUTIVE = 4
BONUS_FIRST_CHAR = 8
PENALTY_GAP_START = 3
PENALTY_GAP_EXTENSION = 1

TOP_LEVEL_CACHE_LIMIT = 100
MAX_QUERY_LEN = 64
CHUNK_MS = 4


def _is_boundary(prev: str, curr: str) -> bool:
    """Check if current char is at a word boundary."""
    if not prev:
        return True
    if prev in "/_-.":
        return True
    return bool(prev.islower() and curr.isupper())


def _score_path(path: str, query: str) -> float | None:
    """Score a path against a query.

    Returns None if no match, otherwise a score where lower is better.
    """
    query_lower = query.lower()
    path_lower = path.lower()

    # Quick check: all query chars must be present
    for c in query_lower:
        if c not in path_lower:
            return None

    # Find matches and calculate score
    score = 0.0
    qi = 0
    prev_match_pos = -1

    for i, c in enumerate(path_lower):
        if qi < len(query_lower) and c == query_lower[qi]:
            # Match found
            score += SCORE_MATCH

            # Boundary bonus
            if i == 0 or _is_boundary(path[i - 1], path[i]):
                score += BONUS_BOUNDARY

            # Camel case bonus
            if i > 0 and path[i - 1].islower() and path[i].isupper():
                score += BONUS_CAMEL

            # Consecutive bonus
            if prev_match_pos == i - 1:
                score += BONUS_CONSECUTIVE

            # First char bonus
            if qi == 0:
                score += BONUS_FIRST_CHAR

            # Gap penalty
            if prev_match_pos >= 0:
                gap = i - prev_match_pos - 1
                if gap > 0:
                    score -= PENALTY_GAP_START + (gap - 1) * PENALTY_GAP_EXTENSION

            prev_match_pos = i
            qi += 1

    # Did we match all query chars?
    if qi < len(query_lower):
        return None

    # Normalize score (lower is better)
    # Invert so lower score = better match
    return -score


class FileIndex:
    """Fuzzy file search index.

    Provides high-performance fuzzy searching over file paths.
    """

    def __init__(self):
        self._paths: list[str] = []
        self._lower_paths: list[str] = []
        self._ready_count = 0
        self._top_level_cache: list[SearchResult] | None = None

    def load_from_file_list(self, file_list: list[str]) -> None:
        """Load paths from a list of strings.

        Automatically deduplicates paths.
        """
        seen: set[str] = set()
        paths: list[str] = []

        for line in file_list:
            if line and line not in seen:
                seen.add(line)
                paths.append(line)

        self._build_index(paths)

    async def load_from_file_list_async(self, file_list: list[str]) -> None:
        """Async variant that yields to event loop periodically."""
        seen: set[str] = set()
        paths: list[str] = []

        for line in file_list:
            if line and line not in seen:
                seen.add(line)
                paths.append(line)

        await self._build_async(paths)

    def _build_index(self, paths: list[str]) -> None:
        """Build the search index."""
        self._paths = paths
        self._lower_paths = [p.lower() for p in paths]
        self._ready_count = len(paths)
        self._top_level_cache = None

    async def _build_async(self, paths: list[str]) -> None:
        """Build index asynchronously."""
        self._paths = paths
        self._lower_paths = []

        chunk_size = 1000
        for i in range(0, len(paths), chunk_size):
            chunk = paths[i : i + chunk_size]
            self._lower_paths.extend(p.lower() for p in chunk)
            self._ready_count = len(self._lower_paths)
            await asyncio.sleep(0)  # Yield to event loop

        self._top_level_cache = None

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Search for paths matching the query.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            List of SearchResult, sorted by score (best first)
        """
        if not query:
            # Return top-level files (no directories)
            if self._top_level_cache is None:
                top_level = []
                for path in self._paths[: self._ready_count]:
                    if "/" not in path and "\\" not in path:
                        top_level.append(SearchResult(path=path, score=0.0))
                        if len(top_level) >= TOP_LEVEL_CACHE_LIMIT:
                            break
                self._top_level_cache = top_level
            return self._top_level_cache[:limit]

        # Truncate long queries
        query = query[:MAX_QUERY_LEN]

        # Score all paths
        results: list[SearchResult] = []
        for i in range(self._ready_count):
            path = self._paths[i]
            score = _score_path(path, query)
            if score is not None:
                # Apply test penalty
                penalty = 1.0
                if "test" in path.lower():
                    penalty = min(1.0, 1.05)

                results.append(
                    SearchResult(
                        path=path,
                        score=score * penalty,
                    )
                )

        # Sort by score (lower is better)
        results.sort(key=lambda r: r.score)

        # Normalize scores to 0-1 range
        if results:
            for i, r in enumerate(results):
                r.score = i / len(results)

        return results[:limit]

    @property
    def path_count(self) -> int:
        """Get the number of indexed paths."""
        return self._ready_count

    def clear(self) -> None:
        """Clear the index."""
        self._paths = []
        self._lower_paths = []
        self._ready_count = 0
        self._top_level_cache = None
