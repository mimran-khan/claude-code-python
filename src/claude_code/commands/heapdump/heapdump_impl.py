"""Migrated from: commands/heapdump/heapdump.ts"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HeapDumpResult:
    success: bool
    heap_path: str = ""
    diag_path: str = ""
    error: str = ""


async def perform_heap_dump() -> HeapDumpResult:
    """Python uses tracemalloc/objgraph wiring in full port."""
    return HeapDumpResult(success=False, error="Heap dump service not available in Python port")


async def call() -> dict[str, str]:
    result = await perform_heap_dump()
    if not result.success:
        return {"type": "text", "value": f"Failed to create heap dump: {result.error}"}
    return {"type": "text", "value": f"{result.heap_path}\n{result.diag_path}"}
