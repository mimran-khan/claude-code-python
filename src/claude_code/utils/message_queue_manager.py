"""
Unified command queue (module-level) for REPL / SDK drains.

Migrated from: utils/messageQueueManager.ts
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from ..bootstrap.state import get_session_id
from ..types.text_input import (
    ImagePastedContent,
    PastedContent,
    PromptInputMode,
    QueuedCommand,
    QueuePriority,
)
from .messages import extract_text_content
from .session_storage import record_queue_operation
from .signal import create_signal

SetAppState = Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None]

PRIORITY_ORDER: dict[QueuePriority, int] = {"now": 0, "next": 1, "later": 2}

_command_queue: list[QueuedCommand] = []
_snapshot: tuple[QueuedCommand, ...] = ()
_queue_changed = create_signal()


def _notify() -> None:
    global _snapshot
    _snapshot = tuple(_command_queue)
    _queue_changed.emit()


def subscribe_to_command_queue(listener: Callable[[], None]) -> Callable[[], None]:
    return _queue_changed.subscribe(listener)


def get_command_queue_snapshot() -> tuple[QueuedCommand, ...]:
    return _snapshot


def get_command_queue() -> list[QueuedCommand]:
    return list(_command_queue)


def get_command_queue_length() -> int:
    return len(_command_queue)


def has_commands_in_queue() -> bool:
    return bool(_command_queue)


def recheck_command_queue() -> None:
    if _command_queue:
        _notify()


def _log_op(operation: str, content: str | None = None) -> None:
    op: dict[str, Any] = {
        "type": "queue-operation",
        "operation": operation,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "sessionId": str(get_session_id()),
    }
    if content is not None:
        op["content"] = content
    record_queue_operation(op)


def enqueue(command: QueuedCommand) -> None:
    cmd = replace(command, priority=command.priority or "next")
    _command_queue.append(cmd)
    _notify()
    val = cmd.value
    text = val if isinstance(val, str) else None
    _log_op("enqueue", text)


def enqueue_pending_notification(command: QueuedCommand) -> None:
    cmd = replace(command, priority=command.priority or "later")
    _command_queue.append(cmd)
    _notify()
    val = cmd.value
    text = val if isinstance(val, str) else None
    _log_op("enqueue", text)


def dequeue(filter_fn: Callable[[QueuedCommand], bool] | None = None) -> QueuedCommand | None:
    if not _command_queue:
        return None
    best_idx = -1
    best_pri = 10**9
    for i, cmd in enumerate(_command_queue):
        if filter_fn and not filter_fn(cmd):
            continue
        p = PRIORITY_ORDER.get(cmd.priority or "next", 1)
        if p < best_pri:
            best_pri = p
            best_idx = i
    if best_idx < 0:
        return None
    removed = _command_queue.pop(best_idx)
    _notify()
    _log_op("dequeue")
    return removed


def dequeue_all() -> list[QueuedCommand]:
    if not _command_queue:
        return []
    out = list(_command_queue)
    _command_queue.clear()
    _notify()
    for _ in out:
        _log_op("dequeue")
    return out


def peek(filter_fn: Callable[[QueuedCommand], bool] | None = None) -> QueuedCommand | None:
    if not _command_queue:
        return None
    best_idx = -1
    best_pri = 10**9
    for i, cmd in enumerate(_command_queue):
        if filter_fn and not filter_fn(cmd):
            continue
        p = PRIORITY_ORDER.get(cmd.priority or "next", 1)
        if p < best_pri:
            best_pri = p
            best_idx = i
    if best_idx < 0:
        return None
    return _command_queue[best_idx]


def dequeue_all_matching(predicate: Callable[[QueuedCommand], bool]) -> list[QueuedCommand]:
    matched: list[QueuedCommand] = []
    remaining: list[QueuedCommand] = []
    for cmd in _command_queue:
        (matched if predicate(cmd) else remaining).append(cmd)
    if not matched:
        return []
    _command_queue[:] = remaining
    _notify()
    for _ in matched:
        _log_op("dequeue")
    return matched


def remove(commands_to_remove: list[QueuedCommand]) -> None:
    if not commands_to_remove:
        return
    before = len(_command_queue)
    remove_set = set(commands_to_remove)
    _command_queue[:] = [c for c in _command_queue if c not in remove_set]
    if len(_command_queue) != before:
        _notify()
    for _ in commands_to_remove:
        _log_op("remove")


def remove_by_filter(predicate: Callable[[QueuedCommand], bool]) -> list[QueuedCommand]:
    removed: list[QueuedCommand] = []
    keep: list[QueuedCommand] = []
    for cmd in _command_queue:
        if predicate(cmd):
            removed.append(cmd)
        else:
            keep.append(cmd)
    if removed:
        _command_queue[:] = keep
        _notify()
        for _ in removed:
            _log_op("remove")
    return removed


def clear_command_queue() -> None:
    if not _command_queue:
        return
    _command_queue.clear()
    _notify()


def reset_command_queue() -> None:
    global _snapshot
    _command_queue.clear()
    _snapshot = ()


NON_EDITABLE_MODES: set[PromptInputMode] = {"task-notification"}


def is_prompt_input_mode_editable(mode: PromptInputMode) -> bool:
    return mode not in NON_EDITABLE_MODES


def is_queued_command_editable(cmd: QueuedCommand) -> bool:
    return is_prompt_input_mode_editable(cmd.mode) and not cmd.is_meta


def _kairos_channels_enabled() -> bool:
    return __import__("os").environ.get("KAIROS_CHANNELS", "").lower() in ("1", "true", "yes")


def is_queued_command_visible(cmd: QueuedCommand) -> bool:
    if _kairos_channels_enabled() and cmd.origin == "channel":
        return True
    return is_queued_command_editable(cmd)


def _extract_text_from_value(value: str | list[dict[str, Any]]) -> str:
    return value if isinstance(value, str) else extract_text_content(value, "\n")


def _extract_images_from_value(value: str | list[dict[str, Any]], start_id: int) -> list[PastedContent]:
    if isinstance(value, str):
        return []
    images: list[PastedContent] = []
    idx = 0
    for block in value:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "image":
            continue
        src = block.get("source") or {}
        if src.get("type") != "base64":
            continue
        images.append(
            ImagePastedContent(
                id=start_id + idx,
                type="image",
                content=str(src.get("data", "")),
                media_type=str(src.get("media_type", "image/png")),
                filename=f"image{idx + 1}",
            )
        )
        idx += 1
    return images


@dataclass
class PopAllEditableResult:
    text: str
    cursor_offset: int
    images: list[PastedContent]


def _object_group_by(
    items: list[QueuedCommand],
    key_fn: Callable[[QueuedCommand], str],
) -> dict[str, list[QueuedCommand]]:
    groups: dict[str, list[QueuedCommand]] = defaultdict(list)
    for item in items:
        groups[key_fn(item)].append(item)
    return dict(groups)


def pop_all_editable(current_input: str, current_cursor_offset: int) -> PopAllEditableResult | None:
    if not _command_queue:
        return None
    grouped = _object_group_by(
        list(_command_queue),
        lambda c: "editable" if is_queued_command_editable(c) else "nonEditable",
    )
    editable = grouped.get("editable", [])
    non_editable = grouped.get("nonEditable", [])
    if not editable:
        return None
    queued_texts = [_extract_text_from_value(c.value) for c in editable]
    parts = [x for x in [*queued_texts, current_input] if x]
    new_input = "\n".join(parts)
    joined = "\n".join(queued_texts)
    cursor_offset = (len(joined) + (1 if joined and current_input else 0)) + current_cursor_offset
    images: list[PastedContent] = []
    next_id = int(datetime.now().timestamp() * 1000)
    for cmd in editable:
        if cmd.pasted_contents:
            for c in cmd.pasted_contents.values():
                if getattr(c, "type", None) == "image":
                    images.append(c)
        embedded = _extract_images_from_value(cmd.value, next_id)
        images.extend(embedded)
        next_id += len(embedded)
    for c in editable:
        val = c.value
        _log_op("popAll", val if isinstance(val, str) else None)
    _command_queue[:] = non_editable
    _notify()
    return PopAllEditableResult(text=new_input, cursor_offset=cursor_offset, images=images)


subscribe_to_pending_notifications = subscribe_to_command_queue


def get_pending_notifications_snapshot() -> tuple[QueuedCommand, ...]:
    return _snapshot


has_pending_notifications = has_commands_in_queue
get_pending_notifications_count = get_command_queue_length
recheck_pending_notifications = recheck_command_queue


def dequeue_pending_notification() -> QueuedCommand | None:
    return dequeue()


reset_pending_notifications = reset_command_queue
clear_pending_notifications = clear_command_queue


def get_commands_by_max_priority(max_priority: QueuePriority) -> list[QueuedCommand]:
    threshold = PRIORITY_ORDER[max_priority]
    return [c for c in _command_queue if PRIORITY_ORDER.get(c.priority or "next", 1) <= threshold]


def is_slash_command(cmd: QueuedCommand) -> bool:
    if not isinstance(cmd.value, str):
        return False
    v = cmd.value.strip()
    return v.startswith("/") and not cmd.skip_slash_commands
