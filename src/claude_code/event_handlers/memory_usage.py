"""
Process memory sampling for high-RSS warnings.

Migrated from: hooks/useMemoryUsage.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MemoryUsageStatus = Literal["normal", "high", "critical"]

HIGH_BYTES = int(1.5 * 1024 * 1024 * 1024)
CRITICAL_BYTES = int(2.5 * 1024 * 1024 * 1024)


@dataclass(frozen=True)
class MemoryUsageInfo:
    heap_used: int
    status: MemoryUsageStatus


def memory_usage_from_heap(heap_used: int) -> MemoryUsageInfo | None:
    """Return None when normal (TS hook hides normal to avoid UI churn)."""
    if heap_used >= CRITICAL_BYTES:
        return MemoryUsageInfo(heap_used=heap_used, status="critical")
    if heap_used >= HIGH_BYTES:
        return MemoryUsageInfo(heap_used=heap_used, status="high")
    return None
