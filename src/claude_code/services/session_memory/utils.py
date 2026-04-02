"""
Session memory utilities.

Configuration and threshold checking.

Migrated from: services/SessionMemory/sessionMemoryUtils.ts
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from ...bootstrap.state import get_session_id
from ...utils.session_storage import get_session_memory_summary_path
from ..analytics.index import log_event

EXTRACTION_WAIT_TIMEOUT_S = 15.0
EXTRACTION_STALE_THRESHOLD_S = 60.0

_last_summarized_message_id: str | None = None
_extraction_started_at: float | None = None
_tokens_at_last_extraction = 0
_session_memory_initialized = False


@dataclass
class SessionMemoryConfig:
    """Configuration for session memory."""

    enabled: bool = True
    initialization_threshold: int = 5  # Messages before first extraction
    update_threshold: int = 10  # Messages between updates
    min_tool_calls: int = 3  # Minimum tool calls before extraction
    max_memory_size: int = 10000  # Max memory size in chars


DEFAULT_SESSION_MEMORY_CONFIG = SessionMemoryConfig()


def has_met_initialization_threshold(
    messages: list[dict[str, Any]],
    config: SessionMemoryConfig = DEFAULT_SESSION_MEMORY_CONFIG,
) -> bool:
    """
    Check if initialization threshold is met.

    Args:
        messages: Conversation messages
        config: Configuration

    Returns:
        True if threshold met
    """
    return len(messages) >= config.initialization_threshold


def has_met_update_threshold(
    messages: list[dict[str, Any]],
    config: SessionMemoryConfig = DEFAULT_SESSION_MEMORY_CONFIG,
) -> bool:
    """
    Check if update threshold is met.

    Args:
        messages: Conversation messages
        config: Configuration

    Returns:
        True if threshold met
    """
    if len(messages) < config.update_threshold:
        return False

    # Also check tool call count
    tool_calls = get_tool_calls_between_updates(messages)
    return tool_calls >= config.min_tool_calls


def get_tool_calls_between_updates(
    messages: list[dict[str, Any]],
) -> int:
    """
    Count tool calls in messages.

    Args:
        messages: Conversation messages

    Returns:
        Number of tool calls
    """
    count = 0

    for msg in messages:
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                if block.get("type") == "tool_use":
                    count += 1

    return count


def count_messages_since_last_update(
    messages: list[dict[str, Any]],
    last_message_id: str,
) -> int:
    """
    Count messages since last update.

    Args:
        messages: Conversation messages
        last_message_id: ID of last summarized message

    Returns:
        Number of messages since
    """
    found = False
    count = 0

    for msg in messages:
        msg_id = msg.get("id", msg.get("uuid"))

        if found:
            count += 1
        elif msg_id == last_message_id:
            found = True

    return count if found else len(messages)


def get_last_summarized_message_id() -> str | None:
    """Message UUID up to which session memory is current."""
    return _last_summarized_message_id


def set_last_summarized_message_id(message_id: str | None) -> None:
    global _last_summarized_message_id
    _last_summarized_message_id = message_id


def mark_extraction_started() -> None:
    global _extraction_started_at
    import time

    _extraction_started_at = time.time()


def mark_extraction_completed() -> None:
    global _extraction_started_at
    _extraction_started_at = None


async def wait_for_session_memory_extraction() -> None:
    """Wait up to 15s for in-flight extraction; bail if stale (>60s)."""
    import time

    global _extraction_started_at
    start = time.monotonic()
    while _extraction_started_at is not None:
        age = time.time() - _extraction_started_at
        if age > EXTRACTION_STALE_THRESHOLD_S:
            return
        if time.monotonic() - start > EXTRACTION_WAIT_TIMEOUT_S:
            return
        await asyncio.sleep(1.0)


async def get_session_memory_content() -> str | None:
    """Read persisted session memory (summary.md) for the active session."""
    path = get_session_memory_summary_path(str(get_session_id()))
    try:
        from pathlib import Path

        content = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    log_event(
        "tengu_session_memory_loaded",
        {"content_length": len(content)},
    )
    return content


def get_tokens_at_last_extraction() -> int:
    return _tokens_at_last_extraction


def set_tokens_at_last_extraction(tokens: int) -> None:
    global _tokens_at_last_extraction
    _tokens_at_last_extraction = tokens


def is_session_memory_initialized_flag() -> bool:
    return _session_memory_initialized


def set_session_memory_initialized_flag(value: bool) -> None:
    global _session_memory_initialized
    _session_memory_initialized = value
