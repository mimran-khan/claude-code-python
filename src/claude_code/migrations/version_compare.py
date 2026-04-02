"""
Loose version comparison for migration guards.

Use when comparing dotted numeric versions or embedded dates in model IDs.
For strict PEP 440 semantics, prefer ``packaging.version`` at call sites.
"""

from __future__ import annotations

import re
from functools import total_ordering


def version_tuple_from_string(value: str) -> tuple[int, ...]:
    """
    Extract integer segments from *value* (e.g. ``"1.2.3"`` → ``(1, 2, 3)``).

    Non-digits are ignored; empty input yields ``(0,)``.
    """
    parts = re.findall(r"\d+", value)
    if not parts:
        return (0,)
    return tuple(int(p) for p in parts)


def version_tuple_gte(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    """Lexicographic ``>=`` with infinite zero-padding."""
    max_len = max(len(left), len(right))
    a = left + (0,) * (max_len - len(left))
    b = right + (0,) * (max_len - len(right))
    return a >= b


def version_strings_gte(current: str, minimum: str) -> bool:
    """True if *current* parses to a tuple ``>=`` *minimum*."""
    return version_tuple_gte(
        version_tuple_from_string(current),
        version_tuple_from_string(minimum),
    )


@total_ordering
class MigrationVersion:
    """
    Comparable wrapper for integer migration gates (``migrationVersion`` in global config).
    """

    __slots__ = ("value",)

    def __init__(self, value: int) -> None:
        if value < 0:
            raise ValueError("migration version must be non-negative")
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MigrationVersion):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, MigrationVersion):
            return NotImplemented
        return self.value < other.value
