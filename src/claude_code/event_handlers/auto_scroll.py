"""
Transcript auto-scroll / sticky-bottom behavior (concept from hooks/useVirtualScroll.ts).

Ink scroll subscriptions are replaced with explicit state a TUI or event loop can drive.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AutoScrollState:
    """Tracks whether the view should stay pinned to new output."""

    sticky: bool = True
    scroll_top: float = 0.0
    pending_delta: float = 0.0
    viewport_height: float = 0.0
    content_height: float = 0.0
    _last_max_scroll: float = field(default=0.0, repr=False)

    def max_scroll(self) -> float:
        return max(0.0, self.content_height - self.viewport_height)

    def is_at_bottom(self, epsilon: float = 1.0) -> bool:
        return self.scroll_top + epsilon >= self.max_scroll()

    def user_scrolled(self, new_scroll_top: float) -> None:
        self.scroll_top = new_scroll_top
        self.sticky = self.is_at_bottom()

    def notify_content_resized(self, new_content_height: float) -> float | None:
        """
        When content grows and sticky is True, return scroll delta to apply so the
        viewport remains at the bottom; otherwise None.
        """
        prev_max = self._last_max_scroll
        self.content_height = new_content_height
        new_max = self.max_scroll()
        self._last_max_scroll = new_max
        if not self.sticky:
            return None
        delta = new_max - prev_max
        if delta > 0:
            self.scroll_top = new_max
            self.pending_delta = 0.0
            return delta
        self.scroll_top = new_max
        return None

    def scroll_to_bottom(self) -> None:
        self.sticky = True
        self.scroll_top = self.max_scroll()
        self.pending_delta = 0.0

    def scroll_by(self, delta: float) -> None:
        self.pending_delta += delta
        self.sticky = False
