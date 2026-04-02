"""Anthropic Messages API helpers for QueryEngine (tool defs, history, tool execution)."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

from anthropic import AsyncAnthropic
from anthropic.types import Message, ToolParam

from .tool import Tool, ToolResult, ToolUseContext

if TYPE_CHECKING:
    from .query_engine import NonNullableUsage


def resolve_api_key(config_api_key: str | None) -> str:
    """Return API key from config or environment."""
    key = config_api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key or not str(key).strip():
        raise ValueError("Anthropic API key is required: set QueryEngineConfig.api_key or ANTHROPIC_API_KEY.")
    return str(key).strip()


def build_async_client(
    *,
    api_key: str,
    base_url: str | None,
    injected: AsyncAnthropic | None,
) -> AsyncAnthropic:
    if injected is not None:
        return injected
    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    elif os.environ.get("ANTHROPIC_BASE_URL"):
        kwargs["base_url"] = os.environ["ANTHROPIC_BASE_URL"].strip()
    return AsyncAnthropic(**kwargs)


def tools_to_anthropic_params(tools: Sequence[Tool]) -> list[ToolParam]:
    """Map core Tool instances to Anthropic tool definitions."""
    out: list[ToolParam] = []
    for t in tools:
        out.append(
            cast(
                ToolParam,
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": dict(t.input_schema) if t.input_schema else {"type": "object"},
                },
            )
        )
    return out


def usage_from_message(message: Message) -> NonNullableUsage:
    from .query_engine import NonNullableUsage

    u = message.usage
    if u is None:
        return NonNullableUsage()
    return NonNullableUsage(
        input_tokens=int(getattr(u, "input_tokens", 0) or 0),
        output_tokens=int(getattr(u, "output_tokens", 0) or 0),
        cache_creation_input_tokens=int(getattr(u, "cache_creation_input_tokens", 0) or 0),
        cache_read_input_tokens=int(getattr(u, "cache_read_input_tokens", 0) or 0),
    )


def normalize_user_content(prompt: str | list[Any]) -> str | list[dict[str, Any]]:
    if isinstance(prompt, str):
        return prompt
    return cast(list[dict[str, Any]], prompt)


def tool_result_content_str(data: Any) -> str:
    if isinstance(data, str):
        return data
    try:
        return json.dumps(data, default=str)
    except (TypeError, ValueError):
        return str(data)


def find_tool(tools: Sequence[Tool], name: str) -> Tool | None:
    for t in tools:
        if t.name == name:
            return t
        if name in (getattr(t, "aliases", None) or []):
            return t
    return None


async def execute_tool_uses(
    *,
    message: Message,
    tools: Sequence[Tool],
    context: ToolUseContext,
    can_use_tool: Any | None,
    permission_denials: list[Any],
) -> list[dict[str, Any]]:
    """Run each tool_use block and build tool_result content blocks."""
    blocks: list[dict[str, Any]] = []
    for block in message.content:
        if block.type != "tool_use":
            continue
        tool_name = block.name
        tool_use_id = block.id
        raw_input = block.input
        tool_input: dict[str, Any] = raw_input if isinstance(raw_input, dict) else {}

        if can_use_tool is not None:
            try:
                decision = can_use_tool(tool_name, tool_input)
            except Exception as exc:  # noqa: BLE001 — surface as tool error
                blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": f"Permission check failed: {exc}",
                        "is_error": True,
                    }
                )
                continue
            allowed = True
            if isinstance(decision, dict):
                allowed = bool(decision.get("allowed", True))
            if not allowed:
                from .query_engine import SDKPermissionDenial

                permission_denials.append(
                    SDKPermissionDenial(
                        tool_name=tool_name,
                        tool_use_id=tool_use_id,
                        tool_input=tool_input,
                    )
                )
                blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": "Tool use was not permitted.",
                        "is_error": True,
                    }
                )
                continue

        tool = find_tool(tools, tool_name)
        if tool is None:
            blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": f"Unknown tool: {tool_name}",
                    "is_error": True,
                }
            )
            continue

        try:
            result: ToolResult[Any] = await tool.call(tool_input, context, None)
            blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": tool_result_content_str(result.data),
                }
            )
        except Exception as exc:  # noqa: BLE001
            blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": str(exc),
                    "is_error": True,
                }
            )
    return blocks


def append_initial_api_messages(initial: list[Any] | None, target: list[dict[str, Any]]) -> None:
    if not initial:
        return
    for item in initial:
        if isinstance(item, dict) and item.get("role") in ("user", "assistant"):
            content = item.get("content")
            if content is not None:
                target.append({"role": item["role"], "content": content})


def is_abort_event(controller: Any) -> bool:
    if controller is None:
        return False
    if isinstance(controller, asyncio.Event):
        return controller.is_set()
    is_set = getattr(controller, "is_set", None)
    if callable(is_set):
        return bool(is_set())
    return False
