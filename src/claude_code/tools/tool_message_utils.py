"""Shared helpers for tagging messages with tool use IDs. Migrated from tools/utils.ts."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class UserMessage(TypedDict, total=False):
    type: Literal["user"]
    content: Any
    source_tool_use_id: str


class AttachmentMessage(TypedDict, total=False):
    type: Literal["attachment"]
    content: Any
    source_tool_use_id: str


class SystemMessage(TypedDict, total=False):
    type: Literal["system"]
    content: Any
    source_tool_use_id: str


class ToolUseBlock(TypedDict, total=False):
    type: Literal["tool_use"]
    id: str
    name: str


class AssistantMessage(TypedDict, total=False):
    type: Literal["assistant"]
    message: dict[str, Any]


def tag_messages_with_tool_use_id(
    messages: list[dict[str, Any]],
    tool_use_id: str | None,
) -> list[dict[str, Any]]:
    """Tag user messages with source_tool_use_id so they stay transient until the tool resolves."""
    if not tool_use_id:
        return messages
    out: list[dict[str, Any]] = []
    for m in messages:
        if m.get("type") == "user":
            mm = dict(m)
            mm["source_tool_use_id"] = tool_use_id
            out.append(mm)
        else:
            out.append(m)
    return out


def get_tool_use_id_from_parent_message(
    parent_message: dict[str, Any],
    tool_name: str,
) -> str | None:
    """Extract the tool use ID from a parent assistant message for a given tool name."""
    msg = parent_message.get("message") or {}
    content = msg.get("content")
    if not isinstance(content, list):
        return None
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_use" and block.get("name") == tool_name:
            tid = block.get("id")
            return str(tid) if tid is not None else None
    return None
