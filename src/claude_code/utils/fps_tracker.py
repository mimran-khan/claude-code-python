"""
FPS / frame timing metrics for UI render loops.

Migrated from: utils/fpsTracker.ts
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass


@dataclass
class FpsMetrics:
    average_fps: float
    low_1pct_fps: float


class FpsTracker:
    """Tracks frame durations and derives FPS statistics."""

    def __init__(self) -> None:
        self._frame_durations: list[float] = []
        self._first_render_time: float | None = None
        self._last_render_time: float | None = None

    def record(self, duration_ms: float) -> None:
        now = time.perf_counter() * 1000.0
        if self._first_render_time is None:
            self._first_render_time = now
        self._last_render_time = now
        self._frame_durations.append(duration_ms)

    def get_metrics(self) -> FpsMetrics | None:
        if not self._frame_durations or self._first_render_time is None or self._last_render_time is None:
            return None
        total_time_ms = self._last_render_time - self._first_render_time
        if total_time_ms <= 0:
            return None
        total_frames = len(self._frame_durations)
        average_fps = total_frames / (total_time_ms / 1000.0)
        sorted_d = sorted(self._frame_durations, reverse=True)
        p99_index = max(0, int(math.ceil(len(sorted_d) * 0.01) - 1))
        p99_frame_time_ms = sorted_d[p99_index]
        low_1pct_fps = (1000.0 / p99_frame_time_ms) if p99_frame_time_ms > 0 else 0.0
        return FpsMetrics(
            average_fps=round(average_fps * 100) / 100,
            low_1pct_fps=round(low_1pct_fps * 100) / 100,
        )
