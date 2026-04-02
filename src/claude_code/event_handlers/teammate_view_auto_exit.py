"""
Exit teammate transcript view when task errors or is killed.

Migrated from: hooks/useTeammateViewAutoExit.ts
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


def maybe_auto_exit_teammate_view(
    *,
    viewing_agent_task_id: str | None,
    task: Mapping[str, Any] | None,
    is_in_process_teammate_task: Callable[[Mapping[str, Any]], bool],
    exit_teammate_view: Callable[[Callable[..., None]], None],
    set_app_state: Callable[..., None],
) -> None:
    if not viewing_agent_task_id:
        return
    if task is None:
        exit_teammate_view(set_app_state)
        return
    if not is_in_process_teammate_task(task):
        return
    status = str(task.get("status", ""))
    err = task.get("error")
    if status in ("killed", "failed") or err:
        exit_teammate_view(set_app_state)
        return
    if status not in ("running", "completed", "pending"):
        exit_teammate_view(set_app_state)
