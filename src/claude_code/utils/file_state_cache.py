"""
LRU cache of read-file state (content, offsets, partial-view flags).

Migrated from: utils/fileStateCache.ts
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class FileState:
    content: str
    timestamp: float
    offset: int | None
    limit: int | None
    is_partial_view: bool = False


READ_FILE_STATE_CACHE_SIZE = 100
DEFAULT_MAX_CACHE_SIZE_BYTES = 25 * 1024 * 1024


class FileStateCache:
    """
    Normalizes path keys via os.path.normpath and evicts by entry count and
    approximate byte footprint (UTF-8 length of content).
    """

    def __init__(self, max_entries: int, max_size_bytes: int) -> None:
        self._max_entries = max_entries
        self._max_size_bytes = max_size_bytes
        self._order: OrderedDict[str, FileState] = OrderedDict()
        self._calculated_size = 0

    @staticmethod
    def _norm(key: str) -> str:
        import os

        return os.path.normpath(key)

    def _evict_for_size(self, incoming_bytes: int) -> None:
        while self._calculated_size + incoming_bytes > self._max_size_bytes and self._order:
            _, v = self._order.popitem(last=False)
            self._calculated_size -= max(1, len(v.content.encode("utf-8")))
        while len(self._order) >= self._max_entries and self._order:
            _, v = self._order.popitem(last=False)
            self._calculated_size -= max(1, len(v.content.encode("utf-8")))

    def get(self, key: str) -> FileState | None:
        k = self._norm(key)
        if k not in self._order:
            return None
        self._order.move_to_end(k)
        return self._order[k]

    def set(self, key: str, value: FileState) -> FileStateCache:
        k = self._norm(key)
        if k in self._order:
            old = self._order.pop(k)
            self._calculated_size -= max(1, len(old.content.encode("utf-8")))
        size_b = max(1, len(value.content.encode("utf-8")))
        self._evict_for_size(size_b)
        self._order[k] = value
        self._calculated_size += size_b
        return self

    def has(self, key: str) -> bool:
        return self._norm(key) in self._order

    def delete(self, key: str) -> bool:
        k = self._norm(key)
        if k not in self._order:
            return False
        old = self._order.pop(k)
        self._calculated_size -= max(1, len(old.content.encode("utf-8")))
        return True

    def clear(self) -> None:
        self._order.clear()
        self._calculated_size = 0

    @property
    def size(self) -> int:
        return len(self._order)

    @property
    def max(self) -> int:
        return self._max_entries

    @property
    def max_size(self) -> int:
        return self._max_size_bytes

    @property
    def calculated_size(self) -> int:
        return self._calculated_size

    def keys(self) -> Iterator[str]:
        return iter(self._order.keys())

    def entries(self) -> Iterator[tuple[str, FileState]]:
        return iter(self._order.items())

    def dump(self) -> list[tuple[str, FileState]]:
        return list(self._order.items())

    def load(self, entries: list[tuple[str, FileState]]) -> None:
        self.clear()
        for k, v in entries:
            self.set(k, v)


def create_file_state_cache_with_size_limit(
    max_entries: int,
    max_size_bytes: int = DEFAULT_MAX_CACHE_SIZE_BYTES,
) -> FileStateCache:
    return FileStateCache(max_entries, max_size_bytes)


def cache_to_object(cache: FileStateCache) -> dict[str, FileState]:
    return dict(cache.entries())


def cache_keys(cache: FileStateCache) -> list[str]:
    return list(cache.keys())


def clone_file_state_cache(cache: FileStateCache) -> FileStateCache:
    cloned = create_file_state_cache_with_size_limit(cache.max, cache.max_size)
    cloned.load(cache.dump())
    return cloned


def merge_file_state_caches(first: FileStateCache, second: FileStateCache) -> FileStateCache:
    merged = clone_file_state_cache(first)
    for file_path, file_state in second.entries():
        existing = merged.get(file_path)
        if not existing or file_state.timestamp > existing.timestamp:
            merged.set(file_path, file_state)
    return merged
