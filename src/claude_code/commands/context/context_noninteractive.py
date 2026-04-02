"""
Non-interactive /context text output.

Migrated from: commands/context/context-noninteractive.ts
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class CollectContextDataInput:
    messages: list[Any]
    get_app_state: Callable[[], Any]
    options: dict[str, Any]


async def collect_context_data(context: CollectContextDataInput) -> dict[str, Any]:
    """
    Shared data path for slash /context and SDK control requests.

    Full token analysis mirrors query.ts once analyze_context is ported.
    """
    return {
        "categories": [],
        "totalTokens": 0,
        "rawMaxTokens": 200_000,
        "percentage": 0,
        "model": context.options.get("main_loop_model", "unknown"),
        "memoryFiles": [],
        "mcpTools": [],
        "agents": [],
        "skills": {"tokens": 0, "skillFrontmatter": []},
        "messageBreakdown": None,
        "systemTools": [],
        "systemPromptSections": [],
    }


def format_context_as_markdown_table(data: dict[str, Any]) -> str:
    lines = [
        "## Context Usage",
        "",
        f"**Model:** {data.get('model', 'unknown')}  ",
        f"**Tokens:** {data.get('totalTokens', 0)} / {data.get('rawMaxTokens', 0)} ({data.get('percentage', 0)}%)",
        "",
        "_Detailed breakdown requires analyze_context wiring._",
        "",
    ]
    return "\n".join(lines)


async def call(_args: str, context: Any) -> dict[str, str]:
    inp = CollectContextDataInput(
        messages=list(getattr(context, "messages", []) or []),
        get_app_state=context.get_app_state,
        options=getattr(context, "options", {}) or {},
    )
    data = await collect_context_data(inp)
    return {"type": "text", "value": format_context_as_markdown_table(data)}


__all__ = [
    "CollectContextDataInput",
    "call",
    "collect_context_data",
    "format_context_as_markdown_table",
]
