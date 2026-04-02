"""
Agent progress tracking (ported from tasks/LocalAgentTask/LocalAgentTask.tsx).

Replaces React state around ProgressTracker / AgentProgress with plain dataclasses
and update helpers suitable for CLI or MCP event loops.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

MAX_RECENT_ACTIVITIES = 5

SYNTHETIC_OUTPUT_TOOL_NAME = "StructuredOutput"


@dataclass
class ToolActivity:
    tool_name: str
    input: dict[str, object]
    activity_description: str | None = None
    is_search: bool | None = None
    is_read: bool | None = None


@dataclass
class AgentProgress:
    tool_use_count: int
    token_count: int
    last_activity: ToolActivity | None = None
    recent_activities: list[ToolActivity] = field(default_factory=list)
    summary: str | None = None


@dataclass
class ProgressTracker:
    tool_use_count: int = 0
    latest_input_tokens: int = 0
    cumulative_output_tokens: int = 0
    recent_activities: list[ToolActivity] = field(default_factory=list)


def create_progress_tracker() -> ProgressTracker:
    return ProgressTracker()


def get_token_count_from_tracker(tracker: ProgressTracker) -> int:
    return tracker.latest_input_tokens + tracker.cumulative_output_tokens


def get_progress_update(tracker: ProgressTracker) -> AgentProgress:
    last = tracker.recent_activities[-1] if tracker.recent_activities else None
    return AgentProgress(
        tool_use_count=tracker.tool_use_count,
        token_count=get_token_count_from_tracker(tracker),
        last_activity=last,
        recent_activities=list(tracker.recent_activities),
    )


def _usage_numbers(usage: dict[str, object]) -> tuple[int, int, int, int]:
    inp = int(usage.get("input_tokens") or 0)
    cache_create = int(usage.get("cache_creation_input_tokens") or 0)
    cache_read = int(usage.get("cache_read_input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    return inp, cache_create, cache_read, out


def update_progress_from_assistant_message(
    tracker: ProgressTracker,
    *,
    usage: dict[str, object] | None,
    content: list[dict[str, object]] | None,
    resolve_activity_description: Callable[[str, dict[str, object]], str | None] | None = None,
) -> None:
    """Update tracker from one assistant message payload (shape matches API message)."""
    if usage:
        inp, cc, cr, out = _usage_numbers(usage)
        tracker.latest_input_tokens = inp + cc + cr
        tracker.cumulative_output_tokens += out

    if not content:
        return

    for block in content:
        if block.get("type") != "tool_use":
            continue
        name = block.get("name")
        if not isinstance(name, str):
            continue
        tracker.tool_use_count += 1
        if name == SYNTHETIC_OUTPUT_TOOL_NAME:
            continue
        raw_in = block.get("input")
        tool_input: dict[str, object] = raw_in if isinstance(raw_in, dict) else {}
        desc = None
        if resolve_activity_description:
            desc = resolve_activity_description(name, tool_input)
        tracker.recent_activities.append(
            ToolActivity(
                tool_name=name,
                input=tool_input,
                activity_description=desc,
            )
        )
    while len(tracker.recent_activities) > MAX_RECENT_ACTIVITIES:
        tracker.recent_activities.pop(0)
