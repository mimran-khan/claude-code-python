"""
Memoization Utilities.

TTL-based and LRU memoization decorators.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class CacheEntry(Generic[T]):
    """A cached value with metadata."""

    value: T
    timestamp: float
    refreshing: bool = False


def memoize_with_ttl(
    cache_lifetime_ms: float = 5 * 60 * 1000,  # 5 minutes
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Create a memoized function with TTL-based caching.

    Implements write-through caching:
    - If cache is fresh, return immediately
    - If cache is stale, return stale value but refresh in background
    - If no cache exists, compute and cache

    Args:
        cache_lifetime_ms: Cache lifetime in milliseconds

    Returns:
        Decorator function
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        cache: dict[str, CacheEntry[T]] = {}

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            key = json.dumps((args, kwargs), sort_keys=True, default=str)
            cached = cache.get(key)
            now = time.time() * 1000  # Convert to ms

            # No cache - compute and store
            if cached is None:
                value = fn(*args, **kwargs)
                cache[key] = CacheEntry(value=value, timestamp=now)
                return value

            # Fresh cache - return immediately
            if now - cached.timestamp <= cache_lifetime_ms:
                return cached.value

            # Stale cache - return stale value (refresh would need async)
            return cached.value

        # Add cache control
        wrapper.cache = type(
            "CacheControl",
            (),
            {
                "clear": lambda: cache.clear(),
            },
        )()

        return wrapper

    return decorator


def memoize_with_ttl_async(
    cache_lifetime_ms: float = 5 * 60 * 1000,  # 5 minutes
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Create a memoized async function with TTL-based caching.

    Args:
        cache_lifetime_ms: Cache lifetime in milliseconds

    Returns:
        Decorator function
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        cache: dict[str, CacheEntry[Any]] = {}
        in_flight: dict[str, asyncio.Task[Any]] = {}

        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = json.dumps((args, kwargs), sort_keys=True, default=str)
            cached = cache.get(key)
            now = time.time() * 1000

            # No cache - compute and store
            if cached is None:
                # Check for in-flight request (dedup)
                if key in in_flight:
                    return await in_flight[key]

                # Start new request
                task = asyncio.create_task(fn(*args, **kwargs))
                in_flight[key] = task

                try:
                    result = await task
                    cache[key] = CacheEntry(value=result, timestamp=now)
                    return result
                finally:
                    in_flight.pop(key, None)

            # Fresh cache
            if now - cached.timestamp <= cache_lifetime_ms:
                return cached.value

            # Stale cache - refresh in background
            if not cached.refreshing:
                cached.refreshing = True

                async def refresh() -> None:
                    try:
                        new_value = await fn(*args, **kwargs)
                        cache[key] = CacheEntry(
                            value=new_value,
                            timestamp=time.time() * 1000,
                        )
                    except Exception:
                        cache.pop(key, None)

                asyncio.create_task(refresh())

            return cached.value

        wrapper.cache = type(
            "CacheControl",
            (),
            {
                "clear": lambda: (cache.clear(), in_flight.clear()),
            },
        )()

        return wrapper

    return decorator


class LRUCache(Generic[T]):
    """LRU cache implementation."""

    def __init__(self, max_size: int = 100):
        self._cache: OrderedDict[str, T] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> T | None:
        """Get a value, updating recency."""
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def peek(self, key: str) -> T | None:
        """Get a value without updating recency."""
        return self._cache.get(key)

    def set(self, key: str, value: T) -> None:
        """Set a value."""
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value

        # Evict if over capacity
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """Delete a key."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def has(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._cache

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


def memoize_with_lru(
    cache_fn: Callable[..., str],
    max_cache_size: int = 100,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Create a memoized function with LRU eviction.

    Args:
        cache_fn: Function to generate cache key from args
        max_cache_size: Maximum cache entries

    Returns:
        Decorator function
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        cache = LRUCache[T](max_size=max_cache_size)

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            key = cache_fn(*args, **kwargs)
            cached = cache.get(key)

            if cached is not None:
                return cached

            result = fn(*args, **kwargs)
            cache.set(key, result)
            return result

        wrapper.cache = type(
            "CacheControl",
            (),
            {
                "clear": cache.clear,
                "size": lambda: cache.size,
                "delete": cache.delete,
                "get": cache.peek,
                "has": cache.has,
            },
        )()

        return wrapper

    return decorator
