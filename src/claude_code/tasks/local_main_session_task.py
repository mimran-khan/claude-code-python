"""
Background main-session query task (Ctrl+B twice).

Migrated from: tasks/LocalMainSessionTask.ts (core registration + completion).
"""

from __future__ import annotations

import secrets
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from ..utils.debug import log_for_debugging
from ..utils.sdk_event_queue import emit_task_terminated_sdk
from .task import SetAppState, create_task_state_base, get_task_output_path

_TASK_ID_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def generate_main_session_task_id() -> str:
    """Task id with ``s`` prefix (main session), 8 random chars."""
    suffix = "".join(_TASK_ID_ALPHABET[b % len(_TASK_ID_ALPHABET)] for b in secrets.token_bytes(8))
    return f"s{suffix}"


@dataclass
class MainSessionAgentStub:
    """Minimal agent definition when none is passed."""

    agent_type: str = "main-session"
    when_to_use: str = "Main session query"
    source: str = "userSettings"

    def get_system_prompt(self) -> str:
        return ""


def register_main_session_task(
    description: str,
    set_app_state: SetAppState,
    *,
    main_thread_agent: Any | None = None,
    existing_abort: Any | None = None,
) -> tuple[str, Any]:
    """
    Register a backgrounded main session task.

    Returns ``(task_id, abort_signal)``.
    """
    task_id = generate_main_session_task_id()
    agent = main_thread_agent or MainSessionAgentStub()
    base = create_task_state_base(task_id, "local_agent", description)
    base_dict = asdict(base)

    abort_controller = existing_abort
    if abort_controller is None:
        try:
            import anyio

            abort_controller = anyio.CancelScope()
        except ImportError:
            abort_controller = object()

    task_state: dict[str, Any] = {
        **base_dict,
        "type": "local_agent",
        "status": "running",
        "agentId": task_id,
        "prompt": description,
        "selectedAgent": agent,
        "agentType": "main-session",
        "abortController": abort_controller,
        "retrieved": False,
        "lastReportedToolCount": 0,
        "lastReportedTokenCount": 0,
        "isBackgrounded": True,
        "pendingMessages": [],
        "retain": False,
        "diskLoaded": False,
        "output_file": get_task_output_path(task_id),
    }

    log_for_debugging(
        f"[LocalMainSessionTask] Registering task {task_id} with description: {description}",
    )

    def add_task(prev: Any) -> Any:
        from dataclasses import is_dataclass, replace

        tasks = dict(getattr(prev, "tasks", {}) or {})
        tasks[task_id] = task_state
        if is_dataclass(prev):
            return replace(prev, tasks=tasks)
        prev.tasks = tasks
        return prev

    set_app_state(add_task)
    signal = getattr(abort_controller, "signal", abort_controller)
    return task_id, signal


def complete_main_session_task(
    task_id: str,
    success: bool,
    set_app_state: SetAppState,
) -> None:
    """Mark task terminal and emit SDK / notification side effects."""
    was_backgrounded = True
    tool_use_id: str | None = None

    def finalize(prev: Any) -> Any:
        nonlocal was_backgrounded, tool_use_id
        from dataclasses import is_dataclass, replace

        tasks = dict(getattr(prev, "tasks", {}) or {})
        task = tasks.get(task_id)
        if not isinstance(task, Mapping):
            return prev
        if task.get("status") != "running":
            return prev
        was_backgrounded = bool(task.get("isBackgrounded", True))
        tool_use_id = task.get("toolUseId") or task.get("tool_use_id")
        new_task = {
            **dict(task),
            "status": "completed" if success else "failed",
            "endTime": time.time() * 1000,
        }
        msgs = task.get("messages")
        if msgs:
            new_task["messages"] = [msgs[-1]]
        tasks[task_id] = new_task
        if is_dataclass(prev):
            return replace(prev, tasks=tasks)
        prev.tasks = tasks
        return prev

    set_app_state(finalize)

    if was_backgrounded:
        log_for_debugging(f"[LocalMainSessionTask] enqueue notification for {task_id}")
    else:
        emit_task_terminated_sdk(
            task_id,
            "completed" if success else "failed",
            {"tool_use_id": tool_use_id, "summary": "Background session"},
        )


__all__ = [
    "complete_main_session_task",
    "generate_main_session_task_id",
    "register_main_session_task",
    "MainSessionAgentStub",
]
