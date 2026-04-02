"""
Set Utilities.

Optimized set operations.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def difference(a: set[T], b: set[T]) -> set[T]:
    """Get elements in a that are not in b.

    Args:
        a: First set
        b: Second set

    Returns:
        Set of elements in a but not in b
    """
    return a - b


def intersects(a: set[T], b: set[T]) -> bool:
    """Check if two sets have any common elements.

    Args:
        a: First set
        b: Second set

    Returns:
        True if sets share at least one element
    """
    if not a or not b:
        return False
    return bool(a & b)


def every(a: set[T], b: set[T]) -> bool:
    """Check if all elements of a are in b.

    Args:
        a: Set to check
        b: Set to check against

    Returns:
        True if a is a subset of b
    """
    return a <= b


def union(a: set[T], b: set[T]) -> set[T]:
    """Get the union of two sets.

    Args:
        a: First set
        b: Second set

    Returns:
        Set containing all elements from both sets
    """
    return a | b


def symmetric_difference(a: set[T], b: set[T]) -> set[T]:
    """Get elements in either set but not both.

    Args:
        a: First set
        b: Second set

    Returns:
        Set of elements in exactly one of the sets
    """
    return a ^ b
