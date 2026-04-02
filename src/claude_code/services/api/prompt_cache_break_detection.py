"""
Client-side prompt cache break detection (pre/post API call phases).

Migrated from: services/api/promptCacheBreakDetection.ts (logic subset).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

MIN_CACHE_MISS_TOKENS = 2000
CACHE_TTL_5MIN_MS = 5 * 60 * 1000
CACHE_TTL_1HOUR_MS = 60 * 60 * 1000
MAX_TRACKED_SOURCES = 10

TRACKED_SOURCE_PREFIXES = (
    "repl_main_thread",
    "sdk",
    "agent:custom",
    "agent:default",
    "agent:builtin",
)

QuerySource = str


def _djb2_hash(s: str) -> int:
    h = 5381
    for c in s:
        h = ((h << 5) + h) + ord(c)
    return h & 0xFFFFFFFF


def _compute_hash(data: Any) -> int:
    return _djb2_hash(json.dumps(data, sort_keys=True, default=str))


def _sanitize_tool_name(name: str) -> str:
    return "mcp" if name.startswith("mcp__") else name


def get_tracking_key(query_source: QuerySource, agent_id: str | None) -> str | None:
    if query_source == "compact":
        return "repl_main_thread"
    for prefix in TRACKED_SOURCE_PREFIXES:
        if query_source.startswith(prefix):
            return agent_id or query_source
    return None


@dataclass
class _PendingChanges:
    system_prompt_changed: bool = False
    tool_schemas_changed: bool = False
    model_changed: bool = False
    added_tool_count: int = 0
    removed_tool_count: int = 0
    previous_model: str = ""
    new_model: str = ""
    build_prev_diffable_content: Callable[[], str] | None = None


@dataclass
class _PreviousState:
    system_hash: int = 0
    tools_hash: int = 0
    tool_names: list[str] = field(default_factory=list)
    model: str = ""
    call_count: int = 0
    pending_changes: _PendingChanges | None = None
    prev_cache_read_tokens: int | None = None
    cache_deletions_pending: bool = False
    build_diffable_content: Callable[[], str] = field(default_factory=lambda: lambda: "")


_previous_state_by_source: dict[str, _PreviousState] = {}


def _strip_cache_control(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        if "cache_control" in item:
            rest = {k: v for k, v in item.items() if k != "cache_control"}
            out.append(rest)
        else:
            out.append(dict(item))
    return out


@dataclass
class PromptStateSnapshot:
    """Observable inputs that affect server-side prompt cache keys."""

    system: list[dict[str, Any]]
    tool_schemas: list[dict[str, Any]]
    query_source: QuerySource
    model: str
    agent_id: str | None = None
    fast_mode: bool | None = None
    betas: list[str] | None = None


def record_prompt_state(snapshot: PromptStateSnapshot) -> None:
    key = get_tracking_key(snapshot.query_source, snapshot.agent_id)
    if not key:
        return
    try:
        stripped_sys = _strip_cache_control([dict(x) for x in snapshot.system])
        stripped_tools = _strip_cache_control([dict(x) for x in snapshot.tool_schemas])
        system_hash = _compute_hash(stripped_sys)
        tools_hash = _compute_hash(stripped_tools)
        tool_names = [t.get("name", "unknown") for t in snapshot.tool_schemas if isinstance(t, dict)]
        prev = _previous_state_by_source.get(key)
        if not prev:
            while len(_previous_state_by_source) >= MAX_TRACKED_SOURCES:
                first = next(iter(_previous_state_by_source))
                del _previous_state_by_source[first]
            _previous_state_by_source[key] = _PreviousState(
                system_hash=system_hash,
                tools_hash=tools_hash,
                tool_names=list(tool_names),
                model=snapshot.model,
                call_count=1,
            )
            return
        prev.call_count += 1
        system_changed = system_hash != prev.system_hash
        tools_changed = tools_hash != prev.tools_hash
        model_changed = snapshot.model != prev.model
        if system_changed or tools_changed or model_changed:
            prev_set = set(prev.tool_names)
            new_set = set(tool_names)
            added = [n for n in tool_names if n not in prev_set]
            removed = [n for n in prev.tool_names if n not in new_set]
            prev.pending_changes = _PendingChanges(
                system_prompt_changed=system_changed,
                tool_schemas_changed=tools_changed,
                model_changed=model_changed,
                added_tool_count=len(added),
                removed_tool_count=len(removed),
                previous_model=prev.model,
                new_model=snapshot.model,
            )
        else:
            prev.pending_changes = None
        prev.system_hash = system_hash
        prev.tools_hash = tools_hash
        prev.tool_names = list(tool_names)
        prev.model = snapshot.model
    except Exception as exc:
        logger.warning("prompt_cache_record_failed", error=str(exc))


async def check_response_for_cache_break(
    query_source: QuerySource,
    cache_read_tokens: int,
    cache_creation_tokens: int,
    messages: list[dict[str, Any]],
    agent_id: str | None = None,
    request_id: str | None = None,
) -> None:
    key = get_tracking_key(query_source, agent_id)
    if not key:
        return
    state = _previous_state_by_source.get(key)
    if not state:
        return
    if "haiku" in state.model.lower():
        return
    prev_read = state.prev_cache_read_tokens
    state.prev_cache_read_tokens = cache_read_tokens
    if prev_read is None:
        return
    if state.cache_deletions_pending:
        state.cache_deletions_pending = False
        state.pending_changes = None
        return
    token_drop = prev_read - cache_read_tokens
    if cache_read_tokens >= prev_read * 0.95 or token_drop < MIN_CACHE_MISS_TOKENS:
        state.pending_changes = None
        return
    changes = state.pending_changes
    parts: list[str] = []
    if changes:
        if changes.model_changed:
            parts.append(f"model changed ({changes.previous_model} → {changes.new_model})")
        if changes.system_prompt_changed:
            parts.append("system prompt changed")
        if changes.tool_schemas_changed:
            parts.append(f"tools changed (+{changes.added_tool_count}/-{changes.removed_tool_count})")
    last_assistant_ms: int | None = None
    for m in reversed(messages):
        if m.get("type") == "assistant":
            ts = m.get("timestamp")
            if isinstance(ts, str):
                from datetime import datetime

                try:
                    last_assistant_ms = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)
                except ValueError:
                    last_assistant_ms = None
            break
    now_ms = __import__("time").time() * 1000
    gap = int(now_ms - last_assistant_ms) if last_assistant_ms is not None else None
    if parts:
        reason = ", ".join(parts)
    elif gap is not None and gap > CACHE_TTL_1HOUR_MS:
        reason = "possible 1h TTL expiry (prompt unchanged)"
    elif gap is not None and gap > CACHE_TTL_5MIN_MS:
        reason = "possible 5min TTL expiry (prompt unchanged)"
    elif gap is not None:
        reason = "likely server-side (prompt unchanged, <5min gap)"
    else:
        reason = "unknown cause"
    logger.warning(
        "prompt_cache_break",
        reason=reason,
        query_source=query_source,
        call_number=state.call_count,
        prev_cache_read_tokens=prev_read,
        cache_read_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
        request_id=request_id or "",
    )
    state.pending_changes = None


def notify_cache_deletion(query_source: QuerySource, agent_id: str | None = None) -> None:
    key = get_tracking_key(query_source, agent_id)
    st = _previous_state_by_source.get(key) if key else None
    if st:
        st.cache_deletions_pending = True


def notify_compaction(query_source: QuerySource, agent_id: str | None = None) -> None:
    key = get_tracking_key(query_source, agent_id)
    st = _previous_state_by_source.get(key) if key else None
    if st:
        st.prev_cache_read_tokens = None


def cleanup_agent_tracking(agent_id: str) -> None:
    _previous_state_by_source.pop(agent_id, None)


def reset_prompt_cache_break_detection() -> None:
    _previous_state_by_source.clear()
