"""
Drain the unified command queue between REPL turns.

Migrated from: utils/queueProcessor.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ..types.text_input import QueuedCommand
from .message_queue_manager import dequeue, dequeue_all_matching, has_commands_in_queue, peek


def _is_slash_command(cmd: QueuedCommand) -> bool:
    val = cmd.value
    if isinstance(val, str):
        return val.strip().startswith("/")
    for block in val:
        if isinstance(block, dict) and block.get("type") == "text":
            t = str(block.get("text", "")).strip()
            return t.startswith("/")
    return False


@dataclass
class ProcessQueueResult:
    processed: bool


async def process_queue_if_ready(
    execute_input: Callable[[list[QueuedCommand]], Awaitable[None]],
) -> ProcessQueueResult:
    """
    Process the next batch from the queue.

    Slash and bash-mode commands run one at a time; other commands with the same
    mode as the peeked head are drained together.
    """

    def is_main_thread(c: QueuedCommand) -> bool:
        return c.agent_id is None

    nxt = peek(is_main_thread)
    if nxt is None:
        return ProcessQueueResult(processed=False)

    if _is_slash_command(nxt) or nxt.mode == "bash":
        cmd = dequeue(is_main_thread)
        if cmd is None:
            return ProcessQueueResult(processed=False)
        await execute_input([cmd])
        return ProcessQueueResult(processed=True)

    target_mode = nxt.mode

    def pred(c: QueuedCommand) -> bool:
        return is_main_thread(c) and not _is_slash_command(c) and c.mode == target_mode

    batch = dequeue_all_matching(pred)
    if not batch:
        return ProcessQueueResult(processed=False)
    await execute_input(batch)
    return ProcessQueueResult(processed=True)


def has_queued_commands() -> bool:
    return has_commands_in_queue()
