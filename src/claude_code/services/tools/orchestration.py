"""
Partition and run tool batches (serial vs concurrent).

Migrated from: services/tools/toolOrchestration.ts
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class MessageUpdate:
    message: Any | None = None
    new_context: Any | None = None


def get_max_tool_use_concurrency() -> int:
    import os

    raw = os.environ.get("CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY", "")
    try:
        return int(raw) if raw else 10
    except ValueError:
        return 10


async def run_tools(
    tool_use_messages: list[dict[str, Any]],
    assistant_messages: list[dict[str, Any]],
    can_use_tool: Callable[..., Awaitable[Any]],
    tool_use_context: Any,
) -> AsyncIterator[MessageUpdate]:
    """
    Placeholder orchestration: processes tools sequentially.

    Full implementation partitions by is_concurrency_safe and matches TS batching.
    """
    _ = assistant_messages
    for tu in tool_use_messages:
        _ = can_use_tool
        yield MessageUpdate(message={"type": "tool_placeholder", "id": tu.get("id")}, new_context=tool_use_context)
