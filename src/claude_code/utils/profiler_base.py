"""
Shared profiler timeline formatting (startup / query / headless profilers).

Migrated from: utils/profilerBase.ts
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass

from .format import format_file_size


@dataclass
class MarkEntry:
    """Single performance mark (Node perf_hooks mark analogue)."""

    name: str
    start_time: float

    @property
    def startTime(self) -> float:
        return self.start_time


class SimplePerformance:
    """Minimal mark list with monotonic times in milliseconds."""

    def __init__(self) -> None:
        self._origin = time.perf_counter()
        self._marks: list[MarkEntry] = []

    def clearMarks(self) -> None:
        self._marks.clear()
        self._origin = time.perf_counter()

    def mark(self, name: str) -> None:
        elapsed_ms = (time.perf_counter() - self._origin) * 1000.0
        self._marks.append(MarkEntry(name=name, start_time=elapsed_ms))

    def getEntriesByType(self, kind: str) -> list[MarkEntry]:
        if kind == "mark":
            return list(self._marks)
        return []


_perf: SimplePerformance | None = None


def get_performance() -> SimplePerformance:
    global _perf
    if _perf is None:
        _perf = SimplePerformance()
    return _perf


def format_ms(ms: float) -> str:
    return f"{ms:.3f}"


def format_timeline_line(
    total_ms: float,
    delta_ms: float,
    name: str,
    memory: dict[str, int] | None,
    total_pad: int,
    delta_pad: int,
    extra: str = "",
) -> str:
    mem_info = ""
    if memory:
        rss = memory.get("rss", 0)
        heap = memory.get("heap_used", memory.get("heapUsed", 0))
        mem_info = f" | RSS: {format_file_size(rss)}, Heap: {format_file_size(heap)}"
    return (
        f"[+{format_ms(total_ms).rjust(total_pad)}ms] "
        f"(+{format_ms(delta_ms).rjust(delta_pad)}ms) {name}{extra}{mem_info}"
    )


def memory_usage_dict() -> dict[str, int]:
    """Best-effort RSS snapshot (cross-platform, no extra deps)."""
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            pass  # bytes
        else:
            rss *= 1024  # Linux: KB → bytes
        return {"rss": int(rss), "heap_used": 0}
    except Exception:
        return {"rss": 0, "heap_used": 0}
