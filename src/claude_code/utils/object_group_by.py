"""
Group iterable items by a key function (Object.groupBy semantics).

Migrated from: utils/objectGroupBy.ts
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K", bound=Hashable)


def object_group_by(
    items: Iterable[T],
    key_selector: Callable[[T, int], K],
) -> dict[K, list[T]]:
    result: dict[K, list[T]] = {}
    for index, item in enumerate(items):
        key = key_selector(item, index)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


__all__ = ["object_group_by"]
