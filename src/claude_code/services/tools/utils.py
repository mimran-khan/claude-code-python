"""
Tool utilities.

Helper functions for tool message handling.

Migrated from: tools/utils.ts (41 lines)
"""

from __future__ import annotations

from typing import Any


def tag_messages_with_tool_use_id(
    messages: list[dict[str, Any]],
    tool_use_id: str | None,
) -> list[dict[str, Any]]:
    """
    Tag user messages with a sourceToolUseID.

    This keeps them transient until the tool resolves, preventing
    the "is running" message from being duplicated in the UI.

    Args:
        messages: List of messages to tag
        tool_use_id: The tool use ID to tag with

    Returns:
        Tagged messages
    """
    if not tool_use_id:
        return messages

    result = []
    for msg in messages:
        if msg.get("type") == "user":
            result.append({**msg, "source_tool_use_id": tool_use_id})
        else:
            result.append(msg)

    return result


def get_tool_use_id_from_parent_message(
    parent_message: dict[str, Any],
    tool_name: str,
) -> str | None:
    """
    Extract the tool use ID from a parent message for a given tool name.

    Args:
        parent_message: The assistant message containing tool uses
        tool_name: The name of the tool to find

    Returns:
        The tool use ID if found, None otherwise
    """
    content = parent_message.get("message", {}).get("content", [])

    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == tool_name:
            return block.get("id")

    return None


def extract_tool_names_from_message(message: dict[str, Any]) -> list[str]:
    """
    Extract all tool names from an assistant message.

    Args:
        message: The assistant message

    Returns:
        List of tool names used in the message
    """
    names = []
    content = message.get("message", {}).get("content", [])

    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            name = block.get("name")
            if name:
                names.append(name)

    return names


def format_tool_input_for_display(
    tool_name: str,
    input_data: dict[str, Any],
    max_length: int = 200,
) -> str:
    """
    Format tool input for display/logging.

    Args:
        tool_name: Name of the tool
        input_data: Tool input parameters
        max_length: Maximum string length

    Returns:
        Formatted string representation
    """
    import json

    try:
        formatted = json.dumps(input_data, indent=2)
        if len(formatted) > max_length:
            return formatted[:max_length] + "..."
        return formatted
    except Exception:
        return str(input_data)[:max_length]
