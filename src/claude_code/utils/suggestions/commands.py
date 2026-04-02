"""
Command suggestions.

Fuzzy matching for command completion.

Migrated from: utils/suggestions/commandSuggestions.ts (568 lines)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CommandSuggestion:
    """A command suggestion."""

    name: str
    description: str
    score: float = 0.0
    source: str | None = None
    aliases: list[str] | None = None


@dataclass
class Command:
    """A command definition (simplified)."""

    name: str
    description: str = ""
    aliases: list[str] | None = None
    is_hidden: bool = False


# Word separators for fuzzy matching
SEPARATORS = re.compile(r"[:_-]")


def _clean_word(word: str) -> str:
    """Clean a word for matching."""
    return re.sub(r"[^\w]", "", word.lower())


def _calculate_match_score(
    query: str,
    target: str,
    is_exact: bool = False,
) -> float:
    """
    Calculate fuzzy match score.

    Args:
        query: Search query
        target: Target string
        is_exact: Whether to require exact match

    Returns:
        Score from 0 to 1
    """
    query = query.lower()
    target = target.lower()

    # Exact match
    if query == target:
        return 1.0

    # Starts with
    if target.startswith(query):
        return 0.9

    # Contains
    if query in target:
        return 0.7

    # Fuzzy substring match
    if _fuzzy_contains(query, target):
        return 0.5

    return 0.0


def _fuzzy_contains(query: str, target: str) -> bool:
    """Check if query fuzzy-matches target."""
    query_idx = 0

    for char in target:
        if query_idx < len(query) and char == query[query_idx]:
            query_idx += 1

    return query_idx == len(query)


def search_commands(
    query: str,
    commands: list[Command],
    max_results: int = 10,
) -> list[CommandSuggestion]:
    """
    Search commands with fuzzy matching.

    Args:
        query: Search query
        commands: Available commands
        max_results: Maximum results to return

    Returns:
        Sorted list of suggestions
    """
    if not query:
        # Return all non-hidden commands
        return [
            CommandSuggestion(
                name=cmd.name,
                description=cmd.description,
                aliases=cmd.aliases,
            )
            for cmd in commands
            if not cmd.is_hidden
        ][:max_results]

    query = query.lower().lstrip("/")
    results: list[tuple[CommandSuggestion, float]] = []

    for cmd in commands:
        if cmd.is_hidden:
            continue

        best_score = 0.0

        # Match against command name
        name_score = _calculate_match_score(query, cmd.name)
        best_score = max(best_score, name_score * 3.0)  # Weight name matches

        # Match against parts
        parts = SEPARATORS.split(cmd.name)
        for part in parts:
            part_score = _calculate_match_score(query, part)
            best_score = max(best_score, part_score * 2.0)

        # Match against aliases
        if cmd.aliases:
            for alias in cmd.aliases:
                alias_score = _calculate_match_score(query, alias)
                best_score = max(best_score, alias_score * 2.0)

        # Match against description
        if cmd.description:
            words = cmd.description.split()
            for word in words:
                word_clean = _clean_word(word)
                if word_clean:
                    word_score = _calculate_match_score(query, word_clean)
                    best_score = max(best_score, word_score * 0.5)

        if best_score > 0.3:  # Threshold
            results.append(
                (
                    CommandSuggestion(
                        name=cmd.name,
                        description=cmd.description,
                        score=best_score,
                        aliases=cmd.aliases,
                    ),
                    best_score,
                )
            )

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)

    return [r[0] for r in results[:max_results]]


def get_command_suggestions(
    query: str,
    commands: list[Command],
    skill_scores: dict[str, float] | None = None,
    max_results: int = 10,
) -> list[CommandSuggestion]:
    """
    Get command suggestions with skill usage weighting.

    Args:
        query: Search query
        commands: Available commands
        skill_scores: Optional skill usage scores
        max_results: Maximum results

    Returns:
        Sorted suggestions
    """
    suggestions = search_commands(query, commands, max_results * 2)

    # Apply skill usage scores if available
    if skill_scores:
        for suggestion in suggestions:
            skill_score = skill_scores.get(suggestion.name, 0.0)
            suggestion.score += skill_score * 0.5

    # Re-sort after applying skill scores
    suggestions.sort(key=lambda x: x.score, reverse=True)

    return suggestions[:max_results]
