"""
Command queue draining when the REPL is idle.

Migrated from: hooks/useQueueProcessor.ts and utils/queueProcessor.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, TypeAlias

QueuedCmd: TypeAlias = Mapping[str, Any]


class QueryGuardLike(Protocol):
    """Reactive guard: True while a query / dispatch is active."""

    def get_snapshot(self) -> bool: ...

    def subscribe(self, on_change: Callable[[], None]) -> Callable[[], None]: ...


def should_run_queue_processor(
    *,
    is_query_active: bool,
    has_active_local_jsx_ui: bool,
    queue_length: int,
) -> bool:
    """Mirror the early returns in ``useQueueProcessor``'s effect."""
    if is_query_active:
        return False
    if has_active_local_jsx_ui:
        return False
    return queue_length != 0


def _agent_id(cmd: QueuedCmd) -> Any:
    return cmd.get("agentId", cmd.get("agent_id"))


def is_main_thread_command(cmd: QueuedCmd) -> bool:
    """Only drain items not addressed to a subagent."""
    return _agent_id(cmd) is None


def is_slash_command(cmd: QueuedCmd) -> bool:
    val = cmd.get("value")
    if isinstance(val, str):
        return val.strip().startswith("/")
    if isinstance(val, Sequence) and not isinstance(val, (str, bytes)):
        for block in val:
            if isinstance(block, Mapping) and block.get("type") == "text":
                t = block.get("text")
                if isinstance(t, str) and t.strip().startswith("/"):
                    return True
    return False


@dataclass(frozen=True, slots=True)
class ProcessQueueResult:
    processed: bool


async def process_queue_if_ready(
    execute_input: Callable[[list[QueuedCmd]], Awaitable[None]],
    *,
    peek: Callable[[Callable[[QueuedCmd], bool]], QueuedCmd | None],
    dequeue: Callable[[Callable[[QueuedCmd], bool]], QueuedCmd | None],
    dequeue_all_matching: Callable[
        [Callable[[QueuedCmd], bool]],
        list[QueuedCmd],
    ],
) -> ProcessQueueResult:
    """
    Drain one logical batch from the unified queue (priority ordering is owned
    by the store implementation).
    """

    def is_main(c: QueuedCmd) -> bool:
        return is_main_thread_command(c)

    nxt = peek(is_main)
    if nxt is None:
        return ProcessQueueResult(False)

    mode = nxt.get("mode")
    if is_slash_command(nxt) or mode == "bash":
        cmd = dequeue(is_main)
        if cmd is None:
            return ProcessQueueResult(False)
        await execute_input([cmd])
        return ProcessQueueResult(True)

    target_mode = nxt.get("mode")

    def same_mode(c: QueuedCmd) -> bool:
        return is_main_thread_command(c) and not is_slash_command(c) and c.get("mode") == target_mode

    commands = dequeue_all_matching(same_mode)
    if len(commands) == 0:
        return ProcessQueueResult(False)
    await execute_input(commands)
    return ProcessQueueResult(True)


async def maybe_process_queue(
    *,
    is_query_active: bool,
    has_active_local_jsx_ui: bool,
    queue_length: int,
    execute_input: Callable[[list[QueuedCmd]], Awaitable[None]],
    peek: Callable[[Callable[[QueuedCmd], bool]], QueuedCmd | None],
    dequeue: Callable[[Callable[[QueuedCmd], bool]], QueuedCmd | None],
    dequeue_all_matching: Callable[
        [Callable[[QueuedCmd], bool]],
        list[QueuedCmd],
    ],
) -> ProcessQueueResult:
    """Run :func:`process_queue_if_ready` only when hook preconditions hold."""
    if not should_run_queue_processor(
        is_query_active=is_query_active,
        has_active_local_jsx_ui=has_active_local_jsx_ui,
        queue_length=queue_length,
    ):
        return ProcessQueueResult(False)
    return await process_queue_if_ready(
        execute_input,
        peek=peek,
        dequeue=dequeue,
        dequeue_all_matching=dequeue_all_matching,
    )
