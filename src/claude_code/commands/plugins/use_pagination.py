"""
Migrated from: commands/plugin/usePagination.ts

Stateless pagination helpers for plugin list UIs (React-free port of scroll window logic).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


DEFAULT_MAX_VISIBLE = 5


@dataclass(frozen=True)
class ScrollPosition:
    current: int
    total: int
    can_scroll_up: bool
    can_scroll_down: bool


def compute_scroll_offset(
    *,
    total_items: int,
    max_visible: int,
    selected_index: int,
    prev_offset: int,
) -> int:
    """Mirror useMemo scroll offset in usePagination."""

    needs_pagination = total_items > max_visible
    if not needs_pagination:
        return 0

    if selected_index < prev_offset:
        return selected_index

    if selected_index >= prev_offset + max_visible:
        return selected_index - max_visible + 1

    max_offset = max(0, total_items - max_visible)
    return min(prev_offset, max_offset)


def visible_slice(items: list[T], *, start: int, end: int, needs_pagination: bool) -> list[T]:
    if not needs_pagination:
        return list(items)
    return items[start:end]


@dataclass
class PaginationState:
    """Mutable scroll offset holder (replaces useRef in TS)."""

    total_items: int
    max_visible: int = DEFAULT_MAX_VISIBLE
    _scroll_offset: int = 0

    def update_for_selection(self, selected_index: int) -> None:
        self._scroll_offset = compute_scroll_offset(
            total_items=self.total_items,
            max_visible=self.max_visible,
            selected_index=selected_index,
            prev_offset=self._scroll_offset,
        )

    @property
    def scroll_offset(self) -> int:
        return self._scroll_offset

    @property
    def needs_pagination(self) -> bool:
        return self.total_items > self.max_visible

    @property
    def start_index(self) -> int:
        return self._scroll_offset

    @property
    def end_index(self) -> int:
        return min(self._scroll_offset + self.max_visible, self.total_items)

    def get_visible_items(self, items: list[T]) -> list[T]:
        return visible_slice(
            items,
            start=self.start_index,
            end=self.end_index,
            needs_pagination=self.needs_pagination,
        )

    def to_actual_index(self, visible_index: int) -> int:
        return self.start_index + visible_index

    def is_on_current_page(self, actual_index: int) -> bool:
        return self.start_index <= actual_index < self.end_index

    def scroll_position(self, selected_index: int) -> ScrollPosition:
        return ScrollPosition(
            current=selected_index + 1,
            total=self.total_items,
            can_scroll_up=self._scroll_offset > 0,
            can_scroll_down=self._scroll_offset + self.max_visible < self.total_items,
        )

    @property
    def total_pages(self) -> int:
        return max(1, (self.total_items + self.max_visible - 1) // self.max_visible)

    @property
    def current_page(self) -> int:
        return self._scroll_offset // self.max_visible


__all__ = [
    "DEFAULT_MAX_VISIBLE",
    "PaginationState",
    "ScrollPosition",
    "compute_scroll_offset",
    "visible_slice",
]
