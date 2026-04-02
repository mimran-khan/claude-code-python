"""
Async dynamic config (GrowthBook) with default until fetch completes.

Migrated from: hooks/useDynamicConfig.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def resolve_dynamic_config(
    config_name: str,
    default: T,
    fetch: Callable[[str, T], Awaitable[T]],
    *,
    skip_in_tests: bool = False,
) -> T:
    if skip_in_tests:
        return default
    return await fetch(config_name, default)
