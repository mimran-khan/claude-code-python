"""
Incremental transcript persistence (length + first-uuid compaction detection).

Migrated from: hooks/useLogMessages.ts
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass
class LogMessagesState:
    last_recorded_length: int = 0
    last_parent_uuid: str | None = None
    first_message_uuid: str | None = None
    call_seq: int = 0


def transcript_slice_plan(
    messages: Sequence[Mapping[str, Any]],
    state: LogMessagesState,
) -> tuple[int, list[Mapping[str, Any]], str | None]:
    """
    Return ``(start_index, slice_messages, parent_hint)`` for ``record_transcript``.

    Caller invokes ``record_transcript`` and updates refs from the async result.
    """
    first_uuid = messages[0].get("uuid") if messages else None
    first_s = str(first_uuid) if first_uuid is not None else None
    prev_len = state.last_recorded_length
    was_first = state.first_message_uuid is None
    is_incremental = (
        first_s is not None and not was_first and first_s == state.first_message_uuid and prev_len <= len(messages)
    )
    start_index = prev_len if is_incremental else 0
    if start_index >= len(messages):
        return start_index, [], state.last_parent_uuid if is_incremental else None
    sl = list(messages) if start_index == 0 else list(messages[start_index:])
    parent = state.last_parent_uuid if is_incremental else None
    return start_index, sl, parent


def advance_log_messages_state(
    state: LogMessagesState,
    messages: Sequence[Mapping[str, Any]],
    *,
    last_parent_uuid: str | None,
) -> None:
    state.last_recorded_length = len(messages)
    state.first_message_uuid = str(messages[0].get("uuid")) if messages else None
    state.last_parent_uuid = last_parent_uuid
    state.call_seq += 1
