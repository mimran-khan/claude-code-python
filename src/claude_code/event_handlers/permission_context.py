"""
Resolve-once guard for async permission flows.

Migrated from: hooks/toolPermission/PermissionContext.ts (createResolveOnce)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class ResolveOnce(Generic[T]):
    def __init__(self, resolve: Callable[[T], None]) -> None:
        self._resolve_fn = resolve
        self._delivered = False
        self._claimed = False

    def resolve(self, value: T) -> None:
        if self._delivered:
            return
        self._delivered = True
        self._claimed = True
        self._resolve_fn(value)

    def is_resolved(self) -> bool:
        return self._claimed

    def claim(self) -> bool:
        if self._claimed:
            return False
        self._claimed = True
        return True


def create_resolve_once(resolve: Callable[[T], None]) -> ResolveOnce[T]:
    return ResolveOnce(resolve)
