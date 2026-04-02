"""
Signal Utilities.

Tiny listener-set primitive for pure event signals (no stored state).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Signal(Generic[T]):
    """A simple event signal with listeners.

    Distinct from a store - there is no snapshot, no get_state.
    Use this when subscribers only need to know "something happened".

    Usage:
        changed = Signal[str]()

        def on_change(value: str) -> None:
            print(f"Changed: {value}")

        unsubscribe = changed.subscribe(on_change)
        changed.emit("user_settings")
        unsubscribe()
    """

    def __init__(self) -> None:
        self._listeners: set[Callable[[T], None]] = set()

    def subscribe(self, listener: Callable[[T], None]) -> Callable[[], None]:
        """Subscribe a listener. Returns an unsubscribe function.

        Args:
            listener: The listener function to call on emit

        Returns:
            A function to unsubscribe the listener
        """
        self._listeners.add(listener)

        def unsubscribe() -> None:
            self._listeners.discard(listener)

        return unsubscribe

    def emit(self, *args: T) -> None:
        """Call all subscribed listeners with the given arguments.

        Args:
            *args: Arguments to pass to listeners
        """
        for listener in self._listeners:
            listener(*args)

    def clear(self) -> None:
        """Remove all listeners."""
        self._listeners.clear()

    def listener_count(self) -> int:
        """Get the number of subscribed listeners."""
        return len(self._listeners)


class VoidSignal:
    """A signal with no arguments.

    Usage:
        changed = VoidSignal()

        def on_change() -> None:
            print("Changed!")

        unsubscribe = changed.subscribe(on_change)
        changed.emit()
    """

    def __init__(self) -> None:
        self._listeners: set[Callable[[], None]] = set()

    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Subscribe a listener. Returns an unsubscribe function."""
        self._listeners.add(listener)

        def unsubscribe() -> None:
            self._listeners.discard(listener)

        return unsubscribe

    def emit(self) -> None:
        """Call all subscribed listeners."""
        for listener in self._listeners:
            listener()

    def clear(self) -> None:
        """Remove all listeners."""
        self._listeners.clear()


def create_signal() -> VoidSignal:
    """Create a new void signal."""
    return VoidSignal()
