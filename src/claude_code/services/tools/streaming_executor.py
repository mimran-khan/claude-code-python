"""
Streaming tool executor with concurrency control.

Migrated from: services/tools/StreamingToolExecutor.ts (structure; integrates with run_tool_use when wired).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ToolStatus(StrEnum):
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    YIELDED = "yielded"


@dataclass
class TrackedTool:
    id: str
    block: dict[str, Any]
    assistant_message: dict[str, Any]
    status: ToolStatus
    is_concurrency_safe: bool
    promise: asyncio.Task[Any] | None = None
    results: list[Any] = field(default_factory=list)
    pending_progress: list[Any] = field(default_factory=list)
    context_modifiers: list[Callable[[Any], Any]] = field(default_factory=list)


class StreamingToolExecutor:
    """
    Buffers tool uses and runs concurrency-safe tools in parallel.

    Full parity with TypeScript requires ToolUseContext and run_tool_use wiring.
    """

    def __init__(
        self,
        tool_definitions: Any,
        can_use_tool: Callable[..., Awaitable[Any]],
        tool_use_context: Any,
    ) -> None:
        self._tools: list[TrackedTool] = []
        self._tool_definitions = tool_definitions
        self._can_use_tool = can_use_tool
        self._ctx = tool_use_context
        self._has_errored = False
        self._discarded = False

    def discard(self) -> None:
        self._discarded = True

    def add_tool(self, block: dict[str, Any], assistant_message: dict[str, Any]) -> None:
        if self._discarded:
            return
        tid = str(block.get("id", ""))
        self._tools.append(
            TrackedTool(
                id=tid,
                block=block,
                assistant_message=assistant_message,
                status=ToolStatus.QUEUED,
                is_concurrency_safe=False,
            )
        )

    async def drain(self) -> list[Any]:
        """Yield ordered results (placeholder until run_tool_use is integrated)."""
        out: list[Any] = []
        for t in self._tools:
            t.status = ToolStatus.COMPLETED
            out.append({"tool_use_id": t.id, "results": t.results})
        return out
