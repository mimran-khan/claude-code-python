"""
Message utilities.

Functions for creating, manipulating, and normalizing messages.

Migrated from: utils/messages.ts (5513 lines) - Core functionality
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from ..constants.messages import NO_CONTENT_MESSAGE

if TYPE_CHECKING:
    pass

INTERRUPT_MESSAGE = "[Request interrupted by user]"
INTERRUPT_MESSAGE_FOR_TOOL_USE = "[Request interrupted by user]"
CANCEL_MESSAGE = "Request cancelled."
REJECT_MESSAGE = "Request rejected."
REJECT_MESSAGE_WITH_REASON_PREFIX = "Rejected:"
SUBAGENT_REJECT_MESSAGE = "Subagent rejected."
SUBAGENT_REJECT_MESSAGE_WITH_REASON_PREFIX = "Subagent rejected:"
PLAN_REJECTION_PREFIX = "Plan rejected:"
NO_RESPONSE_REQUESTED = "No response requested."
SYNTHETIC_MODEL = "<synthetic>"


def generate_uuid() -> str:
    """Generate a new UUID."""
    return str(uuid.uuid4())


def extract_text_content(blocks: list[dict[str, Any]], separator: str = "") -> str:
    """Extract text from content blocks (type == 'text')."""
    parts: list[str] = []
    for b in blocks:
        if isinstance(b, dict) and b.get("type") == "text":
            parts.append(str(b.get("text", "")))
    return separator.join(parts)


def get_content_text(content: str | list[dict[str, Any]]) -> str | None:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        t = extract_text_content(content, "\n").strip()
        return t or None
    return None


def create_assistant_message(
    content: str | list[dict[str, Any]],
    *,
    usage: dict[str, Any] | None = None,
    is_virtual: bool | None = None,
) -> dict[str, Any]:
    """Build a minimal assistant message dict (API-shaped)."""
    if isinstance(content, str):
        text = content if content else NO_CONTENT_MESSAGE
        blocks: list[dict[str, Any]] = [{"type": "text", "text": text}]
    else:
        blocks = list(content)
    msg: dict[str, Any] = {
        "type": "assistant",
        "uuid": generate_uuid(),
        "message": {
            "id": generate_uuid(),
            "type": "message",
            "role": "assistant",
            "model": SYNTHETIC_MODEL,
            "content": blocks,
            "stop_reason": "end_turn",
        },
    }
    if usage is not None:
        msg["message"]["usage"] = usage
    if is_virtual:
        msg["is_virtual"] = True
    return msg


def derive_short_message_id(uuid_str: str) -> str:
    """
    Derive a short stable message ID (6-char base36 string) from a UUID.

    Used for snip tool referencing.
    """
    # Convert first 8 hex chars to int, then to base36
    hex_part = uuid_str.replace("-", "")[:8]
    num = int(hex_part, 16)

    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    for _ in range(6):
        result = chars[num % 36] + result
        num //= 36

    return result


def create_user_message(
    content: str | list[dict[str, Any]],
    tool_use_result: str | None = None,
    source_tool_assistant_uuid: str | None = None,
    is_meta: bool = False,
    is_interruption: bool = False,
) -> dict[str, Any]:
    """
    Create a user message.

    Args:
        content: Message content (string or content blocks)
        tool_use_result: Tool use result if this is a tool response
        source_tool_assistant_uuid: UUID of assistant message that triggered this
        is_meta: Whether this is a meta message
        is_interruption: Whether this is an interruption

    Returns:
        User message dict
    """
    msg_uuid = generate_uuid()

    message: dict[str, Any] = {
        "type": "user",
        "uuid": msg_uuid,
        "message": {
            "role": "user",
            "content": content,
        },
    }

    if tool_use_result is not None:
        message["tool_use_result"] = tool_use_result

    if source_tool_assistant_uuid:
        message["source_tool_assistant_uuid"] = source_tool_assistant_uuid

    if is_meta:
        message["is_meta"] = True

    if is_interruption:
        message["is_interruption"] = True

    return message


def create_user_interruption_message(tool_use: bool = False) -> dict[str, Any]:
    """Create a user interruption message."""
    return create_user_message(
        content="[Request interrupted by user]",
        is_interruption=True,
    )


def create_system_message(
    content: str,
    level: str = "info",
    subtype: str | None = None,
) -> dict[str, Any]:
    """
    Create a system message.

    Args:
        content: Message content
        level: Message level (info, warning, error)
        subtype: Message subtype

    Returns:
        System message dict
    """
    msg_uuid = generate_uuid()

    message: dict[str, Any] = {
        "type": "system",
        "uuid": msg_uuid,
        "level": level,
        "message": {
            "role": "assistant",
            "content": content,
        },
    }

    if subtype:
        message["subtype"] = subtype

    return message


def create_assistant_api_error_message(
    content: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Create an assistant API error message."""
    return {
        "type": "assistant",
        "uuid": generate_uuid(),
        "is_api_error_message": True,
        "api_error": error,
        "message": {
            "role": "assistant",
            "content": content or "An error occurred.",
        },
    }


def create_compact_boundary_message(
    summary: str,
    pre_compact_token_count: int = 0,
    post_compact_token_count: int = 0,
    direction: str | None = None,
) -> dict[str, Any]:
    """Create a compact boundary message."""
    return {
        "type": "system",
        "subtype": "compact_boundary",
        "uuid": generate_uuid(),
        "summary": summary,
        "pre_compact_token_count": pre_compact_token_count,
        "post_compact_token_count": post_compact_token_count,
        "direction": direction,
        "message": {
            "role": "assistant",
            "content": summary,
        },
    }


def create_microcompact_boundary_message(
    trigger: str,
    tokens_freed: int,
    deleted_tokens: int,
    deleted_tool_ids: list[str],
    modified_messages: list[str],
) -> dict[str, Any]:
    """Create a microcompact boundary message."""
    return {
        "type": "system",
        "subtype": "microcompact_boundary",
        "uuid": generate_uuid(),
        "trigger": trigger,
        "tokens_freed": tokens_freed,
        "deleted_tokens": deleted_tokens,
        "deleted_tool_ids": deleted_tool_ids,
        "modified_messages": modified_messages,
    }


def create_tool_use_summary_message(
    summary: str,
    tool_use_ids: list[str],
) -> dict[str, Any]:
    """Create a tool use summary message."""
    return {
        "type": "tool_use_summary",
        "uuid": generate_uuid(),
        "summary": summary,
        "tool_use_ids": tool_use_ids,
    }


def create_attachment_message(attachment: dict[str, Any]) -> dict[str, Any]:
    """Create an attachment message."""
    return {
        "type": "attachment",
        "uuid": generate_uuid(),
        "attachment": attachment,
    }


def get_messages_after_compact_boundary(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Get messages after the last compact boundary.

    Used to get the relevant messages for API calls.
    """
    # Find last compact boundary
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if msg.get("type") == "system" and msg.get("subtype") == "compact_boundary":
            return messages[i:]

    return messages


def is_compact_boundary_message(message: dict[str, Any]) -> bool:
    """Check if a message is a compact boundary."""
    return message.get("type") == "system" and message.get("subtype") == "compact_boundary"


def get_last_assistant_message(
    messages: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Get the last assistant message from a list of messages."""
    for msg in reversed(messages):
        if msg.get("type") == "assistant":
            return msg
    return None


def get_assistant_message_text(message: dict[str, Any]) -> str:
    """Extract text content from an assistant message."""
    content = message.get("message", {}).get("content", [])

    if isinstance(content, str):
        return content

    text_parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(block.get("text", ""))

    return "\n".join(text_parts)


def normalize_messages_for_api(
    messages: list[dict[str, Any]],
    tools: list[Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Normalize messages for the API.

    Filters out non-API messages and normalizes content.
    """
    result = []

    for msg in messages:
        msg_type = msg.get("type")

        # Only include user and assistant messages
        if msg_type == "user":
            result.append(_normalize_user_message(msg))
        elif msg_type == "assistant":
            result.append(_normalize_assistant_message(msg))

    return result


def _normalize_user_message(msg: dict[str, Any]) -> dict[str, Any]:
    """Normalize a user message for the API."""
    content = msg.get("message", {}).get("content", "")

    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": content,
        },
    }


def _normalize_assistant_message(msg: dict[str, Any]) -> dict[str, Any]:
    """Normalize an assistant message for the API."""
    content = msg.get("message", {}).get("content", [])

    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": content,
        },
    }


def strip_signature_blocks(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Strip thinking/signature blocks from messages.

    Used when falling back to a different model that doesn't
    support protected thinking blocks.
    """
    result = []

    for msg in messages:
        if msg.get("type") != "assistant":
            result.append(msg)
            continue

        content = msg.get("message", {}).get("content", [])
        if isinstance(content, str):
            result.append(msg)
            continue

        # Filter out thinking blocks
        filtered_content = [
            block
            for block in content
            if not isinstance(block, dict) or block.get("type") not in ("thinking", "redacted_thinking")
        ]

        if filtered_content:
            result.append(
                {
                    **msg,
                    "message": {
                        **msg.get("message", {}),
                        "content": filtered_content,
                    },
                }
            )

    return result


def count_tool_use_blocks(messages: list[dict[str, Any]]) -> int:
    """Count the number of tool use blocks in messages."""
    count = 0

    for msg in messages:
        if msg.get("type") != "assistant":
            continue

        content = msg.get("message", {}).get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    count += 1

    return count


def extract_tool_use_ids(messages: list[dict[str, Any]]) -> list[str]:
    """Extract all tool use IDs from messages."""
    ids = []

    for msg in messages:
        if msg.get("type") != "assistant":
            continue

        content = msg.get("message", {}).get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_id = block.get("id")
                    if tool_id:
                        ids.append(tool_id)

    return ids
