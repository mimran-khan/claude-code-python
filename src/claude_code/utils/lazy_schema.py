"""
Lazy schema / factory memoization.

Migrated from: utils/lazySchema.ts
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def lazy_schema(factory: Callable[[], T]) -> Callable[[], T]:
    """
    Return a memoized factory that constructs the value on first call.

    Used to defer heavy schema construction from import time to first access.
    """
    cached: T | None = None

    def getter() -> T:
        nonlocal cached
        if cached is None:
            cached = factory()
        return cached

    return getter
