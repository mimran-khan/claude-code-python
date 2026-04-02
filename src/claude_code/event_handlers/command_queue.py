"""
Subscribe to the unified slash / prompt command queue.

Migrated from: hooks/useCommandQueue.ts (useSyncExternalStore over messageQueueManager).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class CommandQueuePort(Protocol[T]):
    """Implement with the host's message-queue snapshot + subscribe."""

    def get_command_queue_snapshot(self) -> T: ...

    def subscribe_to_command_queue(self, on_store_change: Callable[[], None]) -> Callable[[], None]:
        """Return unsubscribe callable."""
        ...


def get_frozen_queue_snapshot(port: CommandQueuePort[list[Any]]) -> tuple[Any, ...]:
    """Return an immutable tuple view for identity-safe comparisons."""
    return tuple(port.get_command_queue_snapshot())
