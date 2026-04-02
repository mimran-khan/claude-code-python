"""
Query dependencies container.

Migrated from: query/deps.ts — includes stream/compact production wiring used by query.py.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryDeps:
    """External dependencies for :func:`claude_code.query.query.query`."""

    tools: dict[str, Any] = field(default_factory=dict)
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    check_permission: Callable[..., Any] | None = None
    log_event: Callable[[str, dict[str, Any]], None] | None = None
    read_file: Callable[[str], str] | None = None
    write_file: Callable[[str, str], None] | None = None
    git_status: Callable[[], Any] | None = None
    get_system_prompt: Callable[[], str] | None = None
    get_context_injection: Callable[[], str] | None = None
    on_tool_start: Callable[[Any], None] | None = None
    on_tool_end: Callable[[Any], None] | None = None
    on_message: Callable[[Any], None] | None = None
    state_store: Any | None = None

    call_model: Callable[..., AsyncIterator[Any]] | None = None
    microcompact: Callable[..., Any] | None = None
    autocompact: Callable[..., Any] | None = None
    uuid: Callable[[], str] = field(default_factory=lambda: lambda: str(uuid.uuid4()))


def create_query_deps(
    tools: dict[str, Any] | None = None,
    mcp_servers: dict[str, Any] | None = None,
    **overrides: Any,
) -> QueryDeps:
    """Build deps, starting from production defaults when overrides are omitted."""
    base = production_deps()
    if tools is not None:
        base.tools = tools
    if mcp_servers is not None:
        base.mcp_servers = mcp_servers
    for key, value in overrides.items():
        if hasattr(base, key):
            setattr(base, key, value)
    return base


async def _production_microcompact(
    messages: list[Any],
    tool_use_context: Any,
    query_source: str,
) -> dict[str, Any]:
    from ..services.compact.micro_compact import run_micro_compact

    result = await run_micro_compact(messages, tool_use_context, query_source)
    return {"messages": result.messages, "compaction_info": result.compaction_info}


async def _production_autocompact(
    messages: list[Any],
    tool_use_context: Any,
    ctx: dict[str, Any],
    query_source: str,
    tracking: Any,
    _snip_tokens_freed: int,
) -> dict[str, Any]:
    """Placeholder autocompact hook; extend when full autoCompact port lands."""
    consecutive = getattr(tracking, "consecutive_failures", None) if tracking else None
    return {"compaction_result": None, "consecutive_failures": consecutive}


async def _adapt_call_model(
    *,
    messages: list[Any],
    system_prompt: str,
    thinking_config: Any = None,
    tools: list[Any],
    signal: Any = None,
    model: str,
    query_source: str,
) -> AsyncIterator[Any]:
    from ..services.api.claude import query_model_with_streaming

    _ = (thinking_config, signal, query_source)
    async for event in query_model_with_streaming(
        messages=messages,
        model=model,
        system=system_prompt,
        tools=tools or None,
    ):
        yield event


def production_deps() -> QueryDeps:
    """Default deps for the query loop (model stream + microcompact)."""
    return QueryDeps(
        call_model=_adapt_call_model,
        microcompact=_production_microcompact,
        autocompact=_production_autocompact,
        uuid=lambda: str(uuid.uuid4()),
    )
