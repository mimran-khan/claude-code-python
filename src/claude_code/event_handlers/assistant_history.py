"""
Lazy-load ``claude assistant`` remote session history (viewer mode).

Migrated from: hooks/useAssistantHistory.ts — constants + message conversion hook-in.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

PREFETCH_THRESHOLD_ROWS = 40
MAX_FILL_PAGES = 10
SENTINEL_LOADING = "loading older messages…"
SENTINEL_LOADING_FAILED = "failed to load older messages — scroll up to retry"
SENTINEL_START = "start of session"


def page_events_to_messages(
    events: Sequence[Any],
    convert_sdk_message: Callable[[Any, dict[str, bool]], Any],
) -> list[Any]:
    """Map history page events to REPL messages (TS: pageToMessages)."""
    out: list[Any] = []
    opts = {"convertUserTextMessages": True, "convertToolResults": True}
    for ev in events:
        converted = convert_sdk_message(ev, opts)
        if getattr(converted, "type", None) == "message":
            out.append(converted.message)
        elif isinstance(converted, dict) and converted.get("type") == "message":
            out.append(converted["message"])
    return out
