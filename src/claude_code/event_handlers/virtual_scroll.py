"""
Virtual list windowing constants for ScrollBox parity.

Migrated from: hooks/useVirtualScroll.ts (constants only; layout math stays in TUI).
"""

from __future__ import annotations

DEFAULT_ESTIMATE = 3
OVERSCAN_ROWS = 80
COLD_START_COUNT = 30
SCROLL_QUANTUM = OVERSCAN_ROWS >> 1
PESSIMISTIC_HEIGHT = 1
MAX_MOUNTED_ITEMS = 300
SLIDE_STEP = 25
