"""
Teammate utilities for agent swarm coordination.

Migrated from: utils/teammate.ts
"""

from __future__ import annotations

import asyncio
import copy
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast

from .env_utils import is_env_truthy
from .teammate_context import (
    get_teammate_context,
)


@dataclass
class DynamicTeamContext:
    agent_id: str
    agent_name: str
    team_name: str
    plan_mode_required: bool
    color: str | None = None
    parent_session_id: str | None = None


_dynamic_team_context: DynamicTeamContext | None = None


def set_dynamic_team_context(context: DynamicTeamContext | None) -> None:
    global _dynamic_team_context
    _dynamic_team_context = context


def clear_dynamic_team_context() -> None:
    global _dynamic_team_context
    _dynamic_team_context = None


def get_dynamic_team_context() -> DynamicTeamContext | None:
    return _dynamic_team_context


def get_parent_session_id() -> str | None:
    in_proc = get_teammate_context()
    if in_proc:
        return in_proc.parent_session_id
    return _dynamic_team_context.parent_session_id if _dynamic_team_context else None


def get_agent_id() -> str | None:
    in_proc = get_teammate_context()
    if in_proc:
        return in_proc.agent_id
    return _dynamic_team_context.agent_id if _dynamic_team_context else None


def get_agent_name() -> str | None:
    in_proc = get_teammate_context()
    if in_proc:
        return in_proc.agent_name
    return _dynamic_team_context.agent_name if _dynamic_team_context else None


def get_team_name(team_context: Mapping[str, Any] | None = None) -> str | None:
    in_proc = get_teammate_context()
    if in_proc:
        return in_proc.team_name
    if _dynamic_team_context and _dynamic_team_context.team_name:
        return _dynamic_team_context.team_name
    if team_context:
        return cast(str | None, team_context.get("teamName"))
    return None


def is_teammate() -> bool:
    if get_teammate_context() is not None:
        return True
    return bool(_dynamic_team_context and _dynamic_team_context.agent_id and _dynamic_team_context.team_name)


def get_teammate_color() -> str | None:
    in_proc = get_teammate_context()
    if in_proc:
        return in_proc.color
    return _dynamic_team_context.color if _dynamic_team_context else None


def is_plan_mode_required() -> bool:
    import os

    in_proc = get_teammate_context()
    if in_proc:
        return in_proc.plan_mode_required
    if _dynamic_team_context is not None:
        return _dynamic_team_context.plan_mode_required
    return is_env_truthy(os.environ.get("CLAUDE_CODE_PLAN_MODE_REQUIRED"))


def is_team_lead(team_context: Mapping[str, Any] | None) -> bool:
    if not team_context:
        return False
    lead_id = team_context.get("leadAgentId")
    if not lead_id:
        return False
    my_id = get_agent_id()
    if my_id == lead_id:
        return True
    return bool(not my_id)


class _InProcessTeammateTask(Protocol):
    type: str
    status: str
    is_idle: bool | None
    on_idle_callbacks: list[Callable[[], None]] | None


class _AppStateTasks(Protocol):
    tasks: Mapping[str, _InProcessTeammateTask]


def _task_field(task: Any, name: str) -> Any:
    if isinstance(task, dict):
        return task.get(name)
    return getattr(task, name, None)


def has_active_in_process_teammates(app_state: _AppStateTasks) -> bool:
    for task in app_state.tasks.values():
        if _task_field(task, "type") == "in_process_teammate" and _task_field(task, "status") == "running":
            return True
    return False


def has_working_in_process_teammates(app_state: _AppStateTasks) -> bool:
    for task in app_state.tasks.values():
        if (
            _task_field(task, "type") == "in_process_teammate"
            and _task_field(task, "status") == "running"
            and not (_task_field(task, "is_idle") or False)
        ):
            return True
    return False


async def wait_for_teammates_to_become_idle(
    set_app_state: Callable[[Callable[[Any], Any]], None],
    app_state: _AppStateTasks,
) -> None:
    """Register on-idle callbacks (dict-shaped tasks, or objects with __dict__)."""

    working_ids: list[str] = []
    for tid, task in app_state.tasks.items():
        if (
            _task_field(task, "type") == "in_process_teammate"
            and _task_field(task, "status") == "running"
            and not (_task_field(task, "is_idle") or False)
        ):
            working_ids.append(str(tid))

    if not working_ids:
        return

    loop = asyncio.get_running_loop()
    done = asyncio.Event()
    remaining = {"n": len(working_ids)}

    def on_idle() -> None:
        remaining["n"] -= 1
        if remaining["n"] <= 0:
            loop.call_soon_threadsafe(done.set)

    def updater(prev: Any) -> Any:
        raw = getattr(prev, "tasks", {})
        new_tasks = dict(raw)
        for task_id in working_ids:
            task = new_tasks.get(task_id)
            if task is None:
                continue
            if _task_field(task, "type") != "in_process_teammate":
                continue
            if _task_field(task, "is_idle"):
                on_idle()
            elif isinstance(task, dict):
                cbs = list(task.get("on_idle_callbacks") or [])
                cbs.append(on_idle)
                new_tasks[task_id] = {**task, "on_idle_callbacks": cbs}
            else:
                cbs = list(getattr(task, "on_idle_callbacks", None) or [])
                cbs.append(on_idle)
                if hasattr(task, "__dataclass_fields__"):
                    from dataclasses import replace

                    new_tasks[task_id] = replace(task, on_idle_callbacks=cbs)
                else:
                    cloned = copy.copy(task)
                    cloned.on_idle_callbacks = cbs
                    new_tasks[task_id] = cloned
        if isinstance(prev, dict):
            return {**prev, "tasks": new_tasks}
        new_prev = copy.copy(prev)
        new_prev.tasks = new_tasks
        return new_prev

    set_app_state(updater)
    await done.wait()
