"""
Async hook registry for deferred hook registration.

Migrated from: utils/hooks/AsyncHookRegistry.ts (simplified).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Hashable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

K = TypeVar("K", bound=Hashable)
T = TypeVar("T")


@dataclass
class AsyncHookRegistry(Generic[K, T]):
    _hooks: dict[K, list[Callable[..., Awaitable[T]]]] = field(default_factory=dict)

    def register(self, key: K, fn: Callable[..., Awaitable[T]]) -> None:
        self._hooks.setdefault(key, []).append(fn)

    async def run_all(self, key: K, *args: object, **kwargs: object) -> list[T]:
        results: list[T] = []
        for fn in self._hooks.get(key, []):
            results.append(await fn(*args, **kwargs))
        return results

    def clear(self, key: K | None = None) -> None:
        if key is None:
            self._hooks.clear()
        else:
            self._hooks.pop(key, None)
