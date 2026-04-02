"""
SDK message adapter for remote sessions.

Migrated from: remote/sdkMessageAdapter.ts
"""

from typing import Any


def adapt_sdk_message(message: dict[str, Any]) -> dict[str, Any]:
    """Adapt SDK message for remote session format.

    Transforms internal message format to remote protocol format.
    """
    msg_type = message.get("type", "unknown")

    if msg_type == "assistant":
        return {
            "type": "assistant_message",
            "content": message.get("content", []),
            "model": message.get("model"),
            "stop_reason": message.get("stop_reason"),
        }

    if msg_type == "user":
        return {
            "type": "user_message",
            "content": message.get("content", []),
        }

    if msg_type == "tool_result":
        return {
            "type": "tool_result",
            "tool_use_id": message.get("tool_use_id"),
            "content": message.get("content"),
            "is_error": message.get("is_error", False),
        }

    if msg_type == "progress":
        return {
            "type": "progress",
            "tool_name": message.get("tool_name"),
            "tool_use_id": message.get("tool_use_id"),
            "progress": message.get("progress"),
        }

    # Pass through unknown types
    return message


def adapt_remote_message(message: dict[str, Any]) -> dict[str, Any]:
    """Adapt remote message to internal SDK format.

    Transforms remote protocol format to internal message format.
    """
    msg_type = message.get("type", "unknown")

    if msg_type == "assistant_message":
        return {
            "type": "assistant",
            "content": message.get("content", []),
            "model": message.get("model"),
            "stop_reason": message.get("stop_reason"),
        }

    if msg_type == "user_message":
        return {
            "type": "user",
            "content": message.get("content", []),
        }

    if msg_type == "tool_result":
        return {
            "type": "tool_result",
            "tool_use_id": message.get("tool_use_id"),
            "content": message.get("content"),
            "is_error": message.get("is_error", False),
        }

    # Pass through unknown types
    return message


def extract_content_blocks(message: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract content blocks from a message."""
    content = message.get("content", [])
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return content
    return []


def get_tool_uses(message: dict[str, Any]) -> list[dict[str, Any]]:
    """Get tool use blocks from a message."""
    content = extract_content_blocks(message)
    return [block for block in content if block.get("type") == "tool_use"]


def get_text_content(message: dict[str, Any]) -> str:
    """Get combined text content from a message."""
    content = extract_content_blocks(message)
    text_blocks = [block.get("text", "") for block in content if block.get("type") == "text"]
    return "\n".join(text_blocks)
