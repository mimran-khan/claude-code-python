"""Group messages at API-round boundaries.

Migrated from: services/compact/grouping.ts
"""

from __future__ import annotations

from typing import Any, Protocol


class _AssistantPayload(Protocol):
    id: str


class _AssistantMessage(Protocol):
    type: str
    message: _AssistantPayload


def group_messages_by_api_round(messages: list[Any]) -> list[list[Any]]:
    groups: list[list[Any]] = []
    current: list[Any] = []
    last_assistant_id: str | None = None
    for msg in messages:
        mtype = getattr(msg, "type", None)
        if mtype == "assistant":
            mid = getattr(getattr(msg, "message", None), "id", None)
            if isinstance(mid, str) and mid != last_assistant_id and current:
                groups.append(current)
                current = [msg]
            else:
                current.append(msg)
            if isinstance(mid, str):
                last_assistant_id = mid
        else:
            current.append(msg)
    if current:
        groups.append(current)
    return groups
