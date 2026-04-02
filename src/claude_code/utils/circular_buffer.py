"""
Fixed-size circular buffer (rolling window).

Migrated from: utils/CircularBuffer.ts

Uses :class:`collections.deque` with ``maxlen`` (TS preallocated array + head index).
"""

from __future__ import annotations

from collections import deque
from typing import Generic, TypeVar

T = TypeVar("T")


class CircularBuffer(Generic[T]):
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._d: deque[T] = deque(maxlen=capacity)

    def add(self, item: T) -> None:
        self._d.append(item)

    def add_all(self, items: list[T]) -> None:
        for item in items:
            self.add(item)

    def get_recent(self, count: int) -> list[T]:
        if count < 1:
            return []
        data = list(self._d)
        n = min(count, len(data))
        return data[-n:]

    def to_array(self) -> list[T]:
        return list(self._d)

    def clear(self) -> None:
        self._d.clear()

    def length(self) -> int:
        return len(self._d)
