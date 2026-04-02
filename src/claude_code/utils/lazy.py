"""
Lazy Initialization Utilities.

Functions for deferring initialization until first access.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Generic, TypeVar

T = TypeVar("T")


def lazy_init(factory: Callable[[], T]) -> Callable[[], T]:
    """Return a memoized factory function that constructs the value on first call.

    Used to defer expensive initialization from module init time to first access.

    Args:
        factory: The function that creates the value

    Returns:
        A function that returns the cached value
    """
    cached: T | None = None
    initialized = False

    @wraps(factory)
    def wrapper() -> T:
        nonlocal cached, initialized
        if not initialized:
            cached = factory()
            initialized = True
        return cached  # type: ignore

    return wrapper


class Lazy(Generic[T]):
    """A lazy wrapper that initializes the value on first access.

    Example:
        expensive_obj = Lazy(lambda: ExpensiveClass())

        # Value is not created yet

        obj = expensive_obj.get()  # Creates the value
        obj2 = expensive_obj.get()  # Returns cached value
    """

    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._value: T | None = None
        self._initialized = False

    def get(self) -> T:
        """Get the value, initializing it if necessary."""
        if not self._initialized:
            self._value = self._factory()
            self._initialized = True
        return self._value  # type: ignore

    def is_initialized(self) -> bool:
        """Check if the value has been initialized."""
        return self._initialized

    def reset(self) -> None:
        """Reset the lazy value so it will be re-initialized on next access."""
        self._value = None
        self._initialized = False
