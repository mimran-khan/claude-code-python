"""
State store implementation.

Migrated from: state/store.ts
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")
Subscriber = Callable[[T], None]


@dataclass
class Store(Generic[T]):
    """Simple observable state store."""

    _state: T
    _subscribers: list[Subscriber[T]] = field(default_factory=list)

    def get_state(self) -> T:
        """Get current state."""
        return self._state

    def set_state(self, new_state: T) -> None:
        """Set new state and notify subscribers."""
        self._state = new_state
        for subscriber in self._subscribers:
            subscriber(self._state)

    def update(self, updater: Callable[[T], T]) -> None:
        """Update state using an updater function."""
        new_state = updater(self._state)
        self.set_state(new_state)

    def subscribe(self, subscriber: Subscriber[T]) -> Callable[[], None]:
        """Subscribe to state changes. Returns unsubscribe function."""
        self._subscribers.append(subscriber)

        def unsubscribe() -> None:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

        return unsubscribe

    def get_snapshot(self) -> T:
        """Get snapshot for React useSyncExternalStore compatibility."""
        return self._state


def create_store(initial_state: T) -> Store[T]:
    """Create a new store with initial state."""
    return Store(_state=initial_state)
