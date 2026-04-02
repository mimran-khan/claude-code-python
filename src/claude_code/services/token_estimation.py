"""
Token estimation services.

Provides functions for counting and estimating tokens in messages and content.

Migrated from: services/tokenEstimation.ts (496 lines)
"""

from __future__ import annotations

import json
from typing import Any

from ..utils.log import log_error


# Alias for compatibility
def estimate_tokens(content):
    return rough_token_count_estimation(content)


def rough_token_count_estimation(
    content: str,
    bytes_per_token: float = 4,
) -> int:
    """
    Rough estimate of token count based on character length.

    Args:
        content: The content to estimate.
        bytes_per_token: Average bytes per token.

    Returns:
        Estimated token count.
    """
    return round(len(content) / bytes_per_token)


def bytes_per_token_for_file_type(file_extension: str) -> float:
    """
    Get estimated bytes-per-token ratio for a file extension.

    Dense JSON has many single-character tokens which makes the
    real ratio closer to 2 rather than the default 4.

    Args:
        file_extension: The file extension (without dot).

    Returns:
        Estimated bytes per token.
    """
    if file_extension in ("json", "jsonl", "jsonc"):
        return 2
    return 4


def rough_token_count_estimation_for_file_type(
    content: str,
    file_extension: str,
) -> int:
    """
    Rough token estimate using file-type-specific bytes-per-token ratio.

    This matters when the API-based token count is unavailable and we
    fall back to the rough estimate.

    Args:
        content: The content to estimate.
        file_extension: The file extension (without dot).

    Returns:
        Estimated token count.
    """
    return rough_token_count_estimation(
        content,
        bytes_per_token_for_file_type(file_extension),
    )


def rough_token_count_estimation_for_content(
    content: str | list[dict[str, Any]] | None,
) -> int:
    """
    Rough token estimate for message content.

    Args:
        content: String or list of content blocks.

    Returns:
        Estimated token count.
    """
    if not content:
        return 0

    if isinstance(content, str):
        return rough_token_count_estimation(content)

    total = 0
    for block in content:
        total += rough_token_count_estimation_for_block(block)

    return total


def rough_token_count_estimation_for_block(
    block: str | dict[str, Any],
) -> int:
    """
    Rough token estimate for a single content block.

    Args:
        block: A content block (string or dict).

    Returns:
        Estimated token count.
    """
    if isinstance(block, str):
        return rough_token_count_estimation(block)

    block_type = block.get("type")

    if block_type == "text":
        return rough_token_count_estimation(block.get("text", ""))

    if block_type in ("image", "document"):
        # Images and PDFs have fixed-ish token costs
        # https://platform.claude.com/docs/en/build-with-claude/vision#calculate-image-costs
        return 2000

    if block_type == "tool_result":
        return rough_token_count_estimation_for_content(block.get("content"))

    if block_type == "tool_use":
        name = block.get("name", "")
        input_data = block.get("input", {})
        return rough_token_count_estimation(name + json.dumps(input_data))

    if block_type == "thinking":
        return rough_token_count_estimation(block.get("thinking", ""))

    if block_type == "redacted_thinking":
        return rough_token_count_estimation(block.get("data", ""))

    # Other block types - serialize and estimate
    return rough_token_count_estimation(json.dumps(block))


def rough_token_count_estimation_for_messages(
    messages: list[dict[str, Any]],
) -> int:
    """
    Rough token estimate for a list of messages.

    Args:
        messages: List of message objects.

    Returns:
        Estimated total token count.
    """
    total = 0
    for message in messages:
        total += rough_token_count_estimation_for_message(message)
    return total


def rough_token_count_estimation_for_message(
    message: dict[str, Any],
) -> int:
    """
    Rough token estimate for a single message.

    Args:
        message: A message object with type and content.

    Returns:
        Estimated token count.
    """
    msg_type = message.get("type")

    if msg_type in ("assistant", "user"):
        inner_message = message.get("message", {})
        content = inner_message.get("content")
        return rough_token_count_estimation_for_content(content)

    if msg_type == "attachment":
        attachment = message.get("attachment")
        if attachment:
            # Simplified - real implementation normalizes attachment
            content = attachment.get("content", "")
            if isinstance(content, str):
                return rough_token_count_estimation(content)
            return rough_token_count_estimation_for_content(content)

    return 0


async def count_tokens_with_api(content: str) -> int | None:
    """
    Count tokens using the Anthropic API.

    Args:
        content: The content to count tokens for.

    Returns:
        Token count, or None if API call fails.
    """
    if not content:
        return 0

    # This would use the anthropic client to count tokens
    # For now, return rough estimate
    try:
        # Placeholder - would call anthropic.beta.messages.countTokens
        return rough_token_count_estimation(content)
    except Exception as e:
        log_error(e)
        return None


async def count_messages_tokens_with_api(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> int | None:
    """
    Count tokens for messages and tools using the Anthropic API.

    Args:
        messages: List of message objects.
        tools: List of tool definitions.

    Returns:
        Token count, or None if API call fails.
    """
    try:
        # Placeholder - would call anthropic.beta.messages.countTokens
        message_tokens = rough_token_count_estimation_for_messages(
            [{"type": "user", "message": {"content": m.get("content")}} for m in messages]
        )
        tool_tokens = sum(rough_token_count_estimation(json.dumps(t)) for t in tools)
        return message_tokens + tool_tokens
    except Exception as e:
        log_error(e)
        return None
