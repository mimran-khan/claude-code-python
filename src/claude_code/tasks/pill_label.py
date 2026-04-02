"""
Background-task footer pill labels.

Migrated from: tasks/pillLabel.ts
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..constants.figures import DIAMOND_FILLED, DIAMOND_OPEN
from ..utils.array import count


def _task_type(task: Mapping[str, object]) -> str:
    return str(task.get("type", ""))


def get_pill_label(tasks: Sequence[Mapping[str, object]]) -> str:
    """Compact label for a set of background tasks (footer / transcript)."""
    n = len(tasks)
    if n == 0:
        return "0 background tasks"
    first_type = _task_type(tasks[0])
    all_same = all(_task_type(t) == first_type for t in tasks)

    if all_same:
        if first_type == "local_bash":
            monitors = count(
                tasks,
                lambda t: _task_type(t) == "local_bash" and t.get("kind") == "monitor",
            )
            shells = n - monitors
            parts: list[str] = []
            if shells > 0:
                parts.append("1 shell" if shells == 1 else f"{shells} shells")
            if monitors > 0:
                parts.append("1 monitor" if monitors == 1 else f"{monitors} monitors")
            return ", ".join(parts)
        if first_type == "in_process_teammate":
            team_names: set[str] = set()
            for t in tasks:
                if _task_type(t) != "in_process_teammate":
                    continue
                ident = t.get("identity")
                if isinstance(ident, Mapping):
                    team_names.add(str(ident.get("teamName", "")))
            team_count = len(team_names) or 1
            return "1 team" if team_count == 1 else f"{team_count} teams"
        if first_type == "local_agent":
            return "1 local agent" if n == 1 else f"{n} local agents"
        if first_type == "remote_agent":
            first = tasks[0]
            if n == 1 and first.get("isUltraplan") is True:
                phase = first.get("ultraplanPhase")
                if phase == "plan_ready":
                    return f"{DIAMOND_FILLED} ultraplan ready"
                if phase == "needs_input":
                    return f"{DIAMOND_OPEN} ultraplan needs your input"
                return f"{DIAMOND_OPEN} ultraplan"
            if n == 1:
                return f"{DIAMOND_OPEN} 1 cloud session"
            return f"{DIAMOND_OPEN} {n} cloud sessions"
        if first_type == "local_workflow":
            return "1 background workflow" if n == 1 else f"{n} background workflows"
        if first_type == "monitor_mcp":
            return "1 monitor" if n == 1 else f"{n} monitors"
        if first_type == "dream":
            return "dreaming"

    return f"{n} background task" if n == 1 else f"{n} background tasks"


def pill_needs_cta(tasks: Sequence[Mapping[str, object]]) -> bool:
    """True when the pill should show the dimmed “ · ↓ to view” hint."""
    if len(tasks) != 1:
        return False
    t = tasks[0]
    return _task_type(t) == "remote_agent" and t.get("isUltraplan") is True and t.get("ultraplanPhase") is not None
