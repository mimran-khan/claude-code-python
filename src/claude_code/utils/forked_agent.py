"""
Forked / subagent query context helpers.

Migrated from: utils/forkedAgent.ts (trimmed; full query parity hooks into query.query).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .debug import log_for_debugging
from .file_state_cache import FileStateCache as LruFileStateCache
from .file_state_cache import clone_file_state_cache

if TYPE_CHECKING:
    from ..core.tool import ToolUseContext


@dataclass
class CacheSafeParams:
    system_prompt: str | list[Any]
    user_context: dict[str, str]
    system_context: dict[str, str]
    tool_use_context: Any
    fork_context_messages: list[Any]


@dataclass
class ForkedAgentParams:
    prompt_messages: list[Any]
    cache_safe_params: CacheSafeParams
    can_use_tool: Callable[..., Any]
    query_source: str
    fork_label: str
    overrides: dict[str, Any] | None = None
    max_output_tokens: int | None = None
    max_turns: int | None = None
    on_message: Callable[[Any], None] | None = None
    skip_transcript: bool = False
    skip_cache_write: bool = False


@dataclass
class ForkedAgentResult:
    messages: list[Any] = field(default_factory=list)
    total_usage: dict[str, int] = field(
        default_factory=lambda: {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }
    )


_last_cache_safe: CacheSafeParams | None = None


def save_cache_safe_params(params: CacheSafeParams | None) -> None:
    global _last_cache_safe
    _last_cache_safe = params


def get_last_cache_safe_params() -> CacheSafeParams | None:
    return _last_cache_safe


def create_get_app_state_with_allowed_tools(
    base_get_app_state: Callable[[], Any],
    allowed_tools: list[str],
) -> Callable[[], Any]:
    if not allowed_tools:
        return base_get_app_state

    def _wrapped() -> Any:
        app = base_get_app_state()
        tpc = getattr(app, "tool_permission_context", None)
        if tpc is None:
            return app
        rules = getattr(tpc, "always_allow_rules", None) or {}
        cmd = list(rules.get("command", []) if isinstance(rules, dict) else [])
        merged_cmd = list(dict.fromkeys([*cmd, *allowed_tools]))
        new_rules = {**rules, "command": merged_cmd} if isinstance(rules, dict) else {"command": merged_cmd}
        try:
            from dataclasses import replace

            new_tpc = replace(tpc, always_allow_rules=new_rules)
            return replace(app, tool_permission_context=new_tpc)
        except Exception:
            return app

    return _wrapped


def create_subagent_context(
    parent_context: ToolUseContext,
    overrides: dict[str, Any] | None = None,
) -> ToolUseContext:
    overrides = overrides or {}
    child = deepcopy(parent_context)
    rfs = overrides.get("read_file_state")
    if isinstance(rfs, LruFileStateCache):
        child.read_file_state = rfs  # type: ignore[assignment]
    elif hasattr(child, "read_file_state"):
        clone_src = overrides.get("read_file_state", parent_context.read_file_state)
        if isinstance(clone_src, LruFileStateCache):
            child.read_file_state = clone_file_state_cache(clone_src)  # type: ignore[assignment]
    if overrides.get("options"):
        child.options = overrides["options"]
    if overrides.get("messages") is not None:
        child.messages = overrides["messages"]
    if overrides.get("agent_id"):
        child.agent_id = overrides["agent_id"]
    if overrides.get("abort_controller"):
        child.abort_controller = overrides["abort_controller"]
    elif not overrides.get("share_abort_controller"):
        child.abort_controller = None
    if overrides.get("get_app_state"):
        child.get_app_state = overrides["get_app_state"]
    qt = parent_context.query_tracking
    from ..core.tool import QueryChainTracking

    child.query_tracking = QueryChainTracking(
        chain_id=str(uuid.uuid4()),
        depth=(qt.depth + 1) if qt else 0,
    )
    return child


async def run_forked_agent(params: ForkedAgentParams) -> ForkedAgentResult:
    """
    Run an isolated forked query loop. Wires to ``query.query`` when available.
    """
    from ..query.query import QueryParams, query

    c = params.cache_safe_params
    isolated = create_subagent_context(
        c.tool_use_context,
        params.overrides,
    )
    initial = [*c.fork_context_messages, *params.prompt_messages]
    out: list[Any] = []
    qp = QueryParams(
        messages=initial,
        system_prompt=c.system_prompt if isinstance(c.system_prompt, str) else str(c.system_prompt),
        user_context=c.user_context,
        system_context=c.system_context,
        can_use_tool=params.can_use_tool,
        tool_use_context=isolated,
        query_source=params.query_source,
        max_output_tokens_override=params.max_output_tokens,
        max_turns=params.max_turns,
        skip_cache_write=params.skip_cache_write,
    )
    usage = ForkedAgentResult().total_usage
    try:
        async for event in query(qp):
            if getattr(event, "type", None) == "stream_event" and hasattr(event, "event"):
                ev = event.event
                if getattr(ev, "type", None) == "message_delta" and getattr(ev, "usage", None):
                    u = ev.usage
                    usage["input_tokens"] += int(getattr(u, "input_tokens", 0) or 0)
                    usage["output_tokens"] += int(getattr(u, "output_tokens", 0) or 0)
                continue
            if getattr(event, "type", None) in ("stream_request_start",):
                continue
            out.append(event)
            if params.on_message:
                params.on_message(event)
    finally:
        log_for_debugging(
            f"Forked agent [{params.fork_label}] finished: {len(out)} messages",
            level="debug",
        )
    return ForkedAgentResult(messages=out, total_usage=usage)


def extract_result_text(agent_messages: list[Any], default_text: str = "Execution completed") -> str:
    for m in reversed(agent_messages):
        role = getattr(m, "role", None)
        if role == "assistant":
            content = getattr(m, "content", "")
            if isinstance(content, str) and content.strip():
                return content.strip()
    return default_text
