"""
Micro compaction.

Handles fine-grained compaction of individual messages and tool results.

Migrated from: services/compact/microCompact.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...types.message import Message


@dataclass
class PendingCacheEdits:
    """Pending cache edits from microcompact."""

    trigger: str = ""
    baseline_cache_deleted_tokens: int = 0
    deleted_tool_ids: list[str] = field(default_factory=list)


@dataclass
class CompactionInfo:
    """Info about microcompaction that occurred."""

    tokens_freed: int = 0
    messages_modified: int = 0
    pending_cache_edits: PendingCacheEdits | None = None


@dataclass
class MicrocompactResult:
    """Result of microcompaction."""

    messages: list[Message]
    compaction_info: CompactionInfo | None = None


async def run_micro_compact(
    messages: list[Message],
    tool_use_context: Any,
    query_source: str,
) -> MicrocompactResult:
    """
    Run microcompaction on messages.

    Microcompaction performs fine-grained optimizations:
    - Truncating large tool results
    - Collapsing repeated similar messages
    - Removing redundant content

    Args:
        messages: Messages to compact
        tool_use_context: Tool use context
        query_source: Query source

    Returns:
        Microcompaction result
    """
    # Check if microcompact is enabled
    import os

    if os.getenv("CLAUDE_CODE_DISABLE_MICROCOMPACT", "").lower() in ("1", "true"):
        return MicrocompactResult(messages=messages)

    # Process messages
    result_messages: list[Message] = []
    tokens_freed = 0
    messages_modified = 0

    for message in messages:
        processed = _process_message(message)
        result_messages.append(processed["message"])
        tokens_freed += processed.get("tokens_freed", 0)
        if processed.get("modified", False):
            messages_modified += 1

    compaction_info = None
    if tokens_freed > 0 or messages_modified > 0:
        compaction_info = CompactionInfo(
            tokens_freed=tokens_freed,
            messages_modified=messages_modified,
        )

    return MicrocompactResult(
        messages=result_messages,
        compaction_info=compaction_info,
    )


def _process_message(message: Message) -> dict[str, Any]:
    """Process a single message for microcompaction."""
    msg_type = message.get("type")

    if msg_type == "user":
        return _process_user_message(message)
    elif msg_type == "assistant":
        return _process_assistant_message(message)
    else:
        return {"message": message, "tokens_freed": 0, "modified": False}


def _process_user_message(message: Message) -> dict[str, Any]:
    """Process a user message for microcompaction."""
    content = message.get("message", {}).get("content", [])

    if isinstance(content, str):
        # Check for truncation opportunity
        if len(content) > 50000:  # ~12.5K tokens
            truncated = content[:50000] + "\n... [content truncated]"
            tokens_freed = (len(content) - 50000) // 4
            return {
                "message": {
                    **message,
                    "message": {
                        **message.get("message", {}),
                        "content": truncated,
                    },
                },
                "tokens_freed": tokens_freed,
                "modified": True,
            }
        return {"message": message, "tokens_freed": 0, "modified": False}

    # Process content blocks
    new_content: list[dict[str, Any]] = []
    tokens_freed = 0
    modified = False

    for block in content:
        if block.get("type") == "tool_result":
            processed = _process_tool_result(block)
            new_content.append(processed["block"])
            tokens_freed += processed.get("tokens_freed", 0)
            if processed.get("modified", False):
                modified = True
        else:
            new_content.append(block)

    if modified:
        return {
            "message": {
                **message,
                "message": {
                    **message.get("message", {}),
                    "content": new_content,
                },
            },
            "tokens_freed": tokens_freed,
            "modified": True,
        }

    return {"message": message, "tokens_freed": 0, "modified": False}


def _process_assistant_message(message: Message) -> dict[str, Any]:
    """Process an assistant message for microcompaction."""
    # Assistant messages typically don't need truncation
    return {"message": message, "tokens_freed": 0, "modified": False}


def _process_tool_result(block: dict[str, Any]) -> dict[str, Any]:
    """Process a tool result for microcompaction."""
    content = block.get("content")

    if isinstance(content, str):
        # Truncate large tool results
        max_result_size = 100000  # ~25K tokens
        if len(content) > max_result_size:
            truncated = content[:max_result_size] + "\n... [output truncated]"
            tokens_freed = (len(content) - max_result_size) // 4
            return {
                "block": {
                    **block,
                    "content": truncated,
                },
                "tokens_freed": tokens_freed,
                "modified": True,
            }

    return {"block": block, "tokens_freed": 0, "modified": False}


def reset_microcompact_state() -> None:
    """Reset module-level microcompact tracking (resetMicrocompactState in TS)."""
    return
