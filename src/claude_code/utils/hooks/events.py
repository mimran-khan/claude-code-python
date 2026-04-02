"""
Hook event system.

Broadcasting hook execution events.

Migrated from: utils/hooks/hookEvents.ts
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

# Hook events that are always emitted
ALWAYS_EMITTED_HOOK_EVENTS = frozenset(["SessionStart", "Setup"])

# All valid hook events
HOOK_EVENTS = frozenset(
    [
        "PreToolUse",
        "PostToolUse",
        "Stop",
        "Notification",
        "SessionStart",
        "Setup",
    ]
)

MAX_PENDING_EVENTS = 100


@dataclass
class HookStartedEvent:
    """Event when a hook starts executing."""

    type: Literal["started"] = "started"
    hook_id: str = ""
    hook_name: str = ""
    hook_event: str = ""


@dataclass
class HookProgressEvent:
    """Event for hook progress/output."""

    type: Literal["progress"] = "progress"
    hook_id: str = ""
    hook_name: str = ""
    hook_event: str = ""
    stdout: str = ""
    stderr: str = ""
    output: str = ""


@dataclass
class HookResponseEvent:
    """Event when a hook completes."""

    type: Literal["response"] = "response"
    hook_id: str = ""
    hook_name: str = ""
    hook_event: str = ""
    output: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    outcome: Literal["success", "error", "cancelled"] = "success"


HookExecutionEvent = HookStartedEvent | HookProgressEvent | HookResponseEvent
HookEventHandler = Callable[[HookExecutionEvent], None]


# Module state
_pending_events: list[HookExecutionEvent] = []
_event_handler: HookEventHandler | None = None
_all_hook_events_enabled: bool = False


def register_hook_event_handler(handler: HookEventHandler | None) -> None:
    """
    Register a handler for hook events.

    Args:
        handler: Handler function or None to unregister
    """
    global _event_handler
    _event_handler = handler

    # Flush pending events
    if handler and _pending_events:
        for event in _pending_events:
            handler(event)
        _pending_events.clear()


def enable_all_hook_events(enabled: bool = True) -> None:
    """Enable or disable emitting all hook events."""
    global _all_hook_events_enabled
    _all_hook_events_enabled = enabled


def _emit(event: HookExecutionEvent) -> None:
    """Emit an event to the handler or queue it."""
    if _event_handler:
        _event_handler(event)
    else:
        _pending_events.append(event)
        if len(_pending_events) > MAX_PENDING_EVENTS:
            _pending_events.pop(0)


def _should_emit(hook_event: str) -> bool:
    """Check if an event should be emitted."""
    if hook_event in ALWAYS_EMITTED_HOOK_EVENTS:
        return True
    return _all_hook_events_enabled and hook_event in HOOK_EVENTS


def emit_hook_started(
    hook_id: str,
    hook_name: str,
    hook_event: str,
) -> None:
    """Emit a hook started event."""
    if not _should_emit(hook_event):
        return

    _emit(
        HookStartedEvent(
            hook_id=hook_id,
            hook_name=hook_name,
            hook_event=hook_event,
        )
    )


def emit_hook_progress(
    hook_id: str,
    hook_name: str,
    hook_event: str,
    stdout: str = "",
    stderr: str = "",
    output: str = "",
) -> None:
    """Emit a hook progress event."""
    if not _should_emit(hook_event):
        return

    _emit(
        HookProgressEvent(
            hook_id=hook_id,
            hook_name=hook_name,
            hook_event=hook_event,
            stdout=stdout,
            stderr=stderr,
            output=output,
        )
    )


def emit_hook_response(
    hook_id: str,
    hook_name: str,
    hook_event: str,
    output: str = "",
    stdout: str = "",
    stderr: str = "",
    exit_code: int | None = None,
    outcome: Literal["success", "error", "cancelled"] = "success",
) -> None:
    """Emit a hook response event."""
    if not _should_emit(hook_event):
        return

    _emit(
        HookResponseEvent(
            hook_id=hook_id,
            hook_name=hook_name,
            hook_event=hook_event,
            output=output,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            outcome=outcome,
        )
    )
