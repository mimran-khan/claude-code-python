"""
Memory relevance finding.

Find relevant memories for a context.

Migrated from: memdir/findRelevantMemories.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from .scan import MemoryFile


@dataclass
class MemoryMatch:
    """A matching memory with relevance score."""

    file: MemoryFile
    score: float
    matched_terms: list[str]


def find_relevant_memories(
    query: str,
    memories: list[MemoryFile],
    max_results: int = 5,
    min_score: float = 0.1,
) -> list[MemoryMatch]:
    """
    Find memories relevant to a query.

    Uses simple keyword matching for now.

    Args:
        query: Search query
        memories: Available memories
        max_results: Maximum results
        min_score: Minimum relevance score

    Returns:
        Sorted list of matches
    """
    query_terms = _tokenize(query.lower())

    if not query_terms:
        return []

    matches: list[MemoryMatch] = []

    for memory in memories:
        if not memory.content:
            continue

        content_lower = memory.content.lower()
        matched_terms: list[str] = []

        for term in query_terms:
            if term in content_lower:
                matched_terms.append(term)

        if matched_terms:
            # Calculate score based on term matches
            score = len(matched_terms) / len(query_terms)

            # Boost for name matches
            name_lower = memory.name.lower()
            for term in query_terms:
                if term in name_lower:
                    score += 0.2

            if score >= min_score:
                matches.append(
                    MemoryMatch(
                        file=memory,
                        score=min(1.0, score),
                        matched_terms=matched_terms,
                    )
                )

    # Sort by score descending
    matches.sort(key=lambda m: m.score, reverse=True)

    return matches[:max_results]


def _tokenize(text: str) -> list[str]:
    """
    Tokenize text into searchable terms.

    Args:
        text: Text to tokenize

    Returns:
        List of terms
    """
    import re

    # Split on non-alphanumeric
    tokens = re.split(r"[^a-z0-9]+", text)

    # Filter short tokens
    return [t for t in tokens if len(t) >= 3]


def rank_memories_by_age(
    memories: list[MemoryFile],
    prefer_recent: bool = True,
) -> list[MemoryFile]:
    """
    Rank memories by file modification time.

    Args:
        memories: Memories to rank
        prefer_recent: Whether to prefer recent files

    Returns:
        Sorted list
    """
    import os

    def get_mtime(m: MemoryFile) -> float:
        try:
            return os.path.getmtime(m.path)
        except OSError:
            return 0.0

    return sorted(
        memories,
        key=get_mtime,
        reverse=prefer_recent,
    )
