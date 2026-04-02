"""
Session-memory-based compaction (experiment).

Migrated from: services/compact/sessionMemoryCompact.ts

Pure index/token helpers and async ``try_session_memory_compaction`` orchestration.
Message shapes follow ``dict`` transcripts (``type`` / ``message`` / ``uuid``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from claude_code.bootstrap.state import get_session_id
from claude_code.services.analytics.growthbook import (
    get_dynamic_config_blocks_on_init,
    get_feature_value_cached_may_be_stale,
)
from claude_code.services.analytics.index import log_event
from claude_code.services.session_memory.prompts import (
    is_session_memory_empty,
    truncate_session_memory_for_compact,
)
from claude_code.services.session_memory.utils import (
    get_last_summarized_message_id,
    get_session_memory_content,
    wait_for_session_memory_extraction,
)
from claude_code.utils.debug import log_for_debugging
from claude_code.utils.env_utils import is_env_truthy
from claude_code.utils.session_storage import get_transcript_path

from .prompt import get_compact_user_summary_message
from .token_utils import estimate_message_tokens


def _is_compact_boundary_message(message: dict[str, Any]) -> bool:
    """Avoid importing message_helpers at module load (circular import via services)."""
    return message.get("type") == "system" and message.get("subtype") == "compact_boundary"


@dataclass
class SessionMemoryCompactConfig:
    """Thresholds for how much transcript tail to keep after SM compact."""

    min_tokens: int = 10_000
    min_text_block_messages: int = 5
    max_tokens: int = 40_000


DEFAULT_SM_COMPACT_CONFIG = SessionMemoryCompactConfig()

_sm_compact_config = SessionMemoryCompactConfig()
_config_initialized = False


def set_session_memory_compact_config(
    config: SessionMemoryCompactConfig | dict[str, Any] | None = None,
) -> None:
    global _sm_compact_config
    if config is None:
        _sm_compact_config = SessionMemoryCompactConfig()
        return
    if isinstance(config, SessionMemoryCompactConfig):
        _sm_compact_config = SessionMemoryCompactConfig(
            min_tokens=config.min_tokens,
            min_text_block_messages=config.min_text_block_messages,
            max_tokens=config.max_tokens,
        )
        return
    base = DEFAULT_SM_COMPACT_CONFIG
    _sm_compact_config = SessionMemoryCompactConfig(
        min_tokens=int(config.get("minTokens") or config.get("min_tokens") or base.min_tokens),
        min_text_block_messages=int(
            config.get("minTextBlockMessages") or config.get("min_text_block_messages") or base.min_text_block_messages
        ),
        max_tokens=int(config.get("maxTokens") or config.get("max_tokens") or base.max_tokens),
    )


def get_session_memory_compact_config() -> SessionMemoryCompactConfig:
    return SessionMemoryCompactConfig(
        min_tokens=_sm_compact_config.min_tokens,
        min_text_block_messages=_sm_compact_config.min_text_block_messages,
        max_tokens=_sm_compact_config.max_tokens,
    )


def reset_session_memory_compact_config() -> None:
    global _sm_compact_config, _config_initialized
    _sm_compact_config = SessionMemoryCompactConfig(
        min_tokens=DEFAULT_SM_COMPACT_CONFIG.min_tokens,
        min_text_block_messages=DEFAULT_SM_COMPACT_CONFIG.min_text_block_messages,
        max_tokens=DEFAULT_SM_COMPACT_CONFIG.max_tokens,
    )
    _config_initialized = False


async def init_session_memory_compact_config() -> None:
    global _config_initialized
    if _config_initialized:
        return
    _config_initialized = True
    remote = await get_dynamic_config_blocks_on_init(
        "tengu_sm_compact_config",
        {},
    )
    if not isinstance(remote, dict):
        return
    cfg = DEFAULT_SM_COMPACT_CONFIG
    mt = remote.get("minTokens") or remote.get("min_tokens")
    mm = remote.get("minTextBlockMessages") or remote.get("min_text_block_messages")
    mx = remote.get("maxTokens") or remote.get("max_tokens")
    set_session_memory_compact_config(
        SessionMemoryCompactConfig(
            min_tokens=int(mt) if mt and int(mt) > 0 else cfg.min_tokens,
            min_text_block_messages=int(mm) if mm and int(mm) > 0 else cfg.min_text_block_messages,
            max_tokens=int(mx) if mx and int(mx) > 0 else cfg.max_tokens,
        )
    )


def has_text_blocks(message: dict[str, Any]) -> bool:
    mtype = message.get("type")
    inner = message.get("message") or {}
    content = inner.get("content")
    if mtype == "assistant" and isinstance(content, list):
        return any(isinstance(b, dict) and b.get("type") == "text" for b in content)
    if mtype == "user":
        if isinstance(content, str):
            return len(content) > 0
        if isinstance(content, list):
            return any(isinstance(b, dict) and b.get("type") == "text" for b in content)
    return False


def _get_tool_result_ids(message: dict[str, Any]) -> list[str]:
    if message.get("type") != "user":
        return []
    content = (message.get("message") or {}).get("content")
    if not isinstance(content, list):
        return []
    out: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_result":
            tid = block.get("tool_use_id")
            if isinstance(tid, str):
                out.append(tid)
    return out


def _has_tool_use_with_ids(message: dict[str, Any], needed: set[str]) -> bool:
    if message.get("type") != "assistant":
        return False
    content = (message.get("message") or {}).get("content")
    if not isinstance(content, list):
        return False
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id") in needed:
            return True
    return False


def adjust_index_to_preserve_api_invariants(
    messages: list[dict[str, Any]],
    start_index: int,
) -> int:
    if start_index <= 0 or start_index >= len(messages):
        return start_index

    adjusted = start_index

    all_tool_result_ids: list[str] = []
    for i in range(adjusted, len(messages)):
        all_tool_result_ids.extend(_get_tool_result_ids(messages[i]))

    if all_tool_result_ids:
        tool_use_in_kept: set[str] = set()
        for i in range(adjusted, len(messages)):
            msg = messages[i]
            if msg.get("type") == "assistant":
                content = (msg.get("message") or {}).get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            bid = block.get("id")
                            if isinstance(bid, str):
                                tool_use_in_kept.add(bid)
        needed = {tid for tid in all_tool_result_ids if tid not in tool_use_in_kept}
        for i in range(adjusted - 1, -1, -1):
            if not needed:
                break
            if _has_tool_use_with_ids(messages[i], needed):
                adjusted = i
                content = (messages[i].get("message") or {}).get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id") in needed:
                            needed.discard(block["id"])

    message_ids_kept: set[str] = set()
    for i in range(adjusted, len(messages)):
        msg = messages[i]
        if msg.get("type") == "assistant":
            mid = (msg.get("message") or {}).get("id")
            if isinstance(mid, str):
                message_ids_kept.add(mid)

    for i in range(adjusted - 1, -1, -1):
        msg = messages[i]
        if msg.get("type") != "assistant":
            continue
        mid = (msg.get("message") or {}).get("id")
        if isinstance(mid, str) and mid in message_ids_kept:
            adjusted = i

    return adjusted


def calculate_messages_to_keep_index(
    messages: list[dict[str, Any]],
    last_summarized_index: int,
) -> int:
    if not messages:
        return 0

    cfg = get_session_memory_compact_config()
    start_index = last_summarized_index + 1 if last_summarized_index >= 0 else len(messages)

    total_tokens = 0
    text_block_count = 0
    for i in range(start_index, len(messages)):
        msg = messages[i]
        total_tokens += estimate_message_tokens(msg)
        if has_text_blocks(msg):
            text_block_count += 1

    if total_tokens >= cfg.max_tokens:
        return adjust_index_to_preserve_api_invariants(messages, start_index)

    if total_tokens >= cfg.min_tokens and text_block_count >= cfg.min_text_block_messages:
        return adjust_index_to_preserve_api_invariants(messages, start_index)

    floor = 0
    for i in range(len(messages) - 1, -1, -1):
        if _is_compact_boundary_message(messages[i]):
            floor = i + 1
            break

    for i in range(start_index - 1, floor - 1, -1):
        msg = messages[i]
        total_tokens += estimate_message_tokens(msg)
        if has_text_blocks(msg):
            text_block_count += 1
        start_index = i
        if total_tokens >= cfg.max_tokens:
            break
        if total_tokens >= cfg.min_tokens and text_block_count >= cfg.min_text_block_messages:
            break

    return adjust_index_to_preserve_api_invariants(messages, start_index)


def should_use_session_memory_compaction() -> bool:
    if is_env_truthy(os.getenv("ENABLE_CLAUDE_CODE_SM_COMPACT")):
        return True
    if is_env_truthy(os.getenv("DISABLE_CLAUDE_CODE_SM_COMPACT")):
        return False
    mem = get_feature_value_cached_may_be_stale("tengu_session_memory", False)
    compact = get_feature_value_cached_may_be_stale("tengu_sm_compact", False)
    use = bool(mem and compact)
    if os.environ.get("USER_TYPE") == "ant":
        log_event(
            "tengu_sm_compact_flag_check",
            {
                "tengu_session_memory": mem,
                "tengu_sm_compact": compact,
                "should_use": use,
            },
        )
    return use


async def try_session_memory_compaction(
    messages: list[dict[str, Any]],
    agent_id: str | None = None,
    auto_compact_threshold: int | None = None,
) -> dict[str, Any] | None:
    """
    Attempt session-memory compaction; returns a compaction result dict or None.

    Keys align with ``query._build_post_compact_messages``:
    ``summary_messages``, ``attachments``, ``hook_results``, ``messages_to_keep``, etc.
    """
    # agent_id reserved for plan attachments when ported from TS createPlanAttachmentIfNeeded
    _ = agent_id
    if not should_use_session_memory_compaction():
        return None

    from claude_code.utils.message_helpers import create_compact_boundary_message

    try:
        await init_session_memory_compact_config()
        await wait_for_session_memory_extraction()

        last_id = get_last_summarized_message_id()
        session_memory = await get_session_memory_content()

        if not session_memory:
            log_event("tengu_sm_compact_no_session_memory", {})
            return None

        if await is_session_memory_empty(session_memory):
            log_event("tengu_sm_compact_empty_template", {})
            return None

        if last_id:
            last_summarized_index = next(
                (i for i, m in enumerate(messages) if m.get("uuid") == last_id),
                -1,
            )
            if last_summarized_index < 0:
                log_event("tengu_sm_compact_summarized_id_not_found", {})
                return None
        else:
            last_summarized_index = len(messages) - 1
            log_event("tengu_sm_compact_resumed_session", {})

        start_index = calculate_messages_to_keep_index(messages, last_summarized_index)
        messages_to_keep = [m for m in messages[start_index:] if not _is_compact_boundary_message(m)]

        truncated, was_truncated = truncate_session_memory_for_compact(session_memory)
        transcript_path = get_transcript_path(get_session_id())
        summary_text = get_compact_user_summary_message(truncated)
        if was_truncated:
            memory_path_note = (
                f"\n\nSome session memory sections were truncated for length. Transcript: {transcript_path}"
            )
            summary_text += memory_path_note

        summary_messages = [
            {
                "type": "user",
                "uuid": None,
                "message": {
                    "role": "user",
                    "content": summary_text,
                },
                "is_compact_summary": True,
                "is_visible_in_transcript_only": True,
            }
        ]

        boundary_marker = create_compact_boundary_message(
            summary="auto",
            pre_compact_token_count=0,
            post_compact_token_count=estimate_message_tokens(summary_messages[0]),
        )

        hook_results: list[Any] = []

        pre_compact_token_count = 0
        post_compact_messages = [boundary_marker, *summary_messages, *messages_to_keep]
        post_compact_token_count = sum(estimate_message_tokens(m) for m in post_compact_messages)

        if auto_compact_threshold is not None and post_compact_token_count >= auto_compact_threshold:
            log_event(
                "tengu_sm_compact_threshold_exceeded",
                {
                    "post_compact_token_count": post_compact_token_count,
                    "auto_compact_threshold": auto_compact_threshold,
                },
            )
            return None

        return {
            "boundary_marker": boundary_marker,
            "summary_messages": summary_messages,
            "attachments": [],
            "hook_results": hook_results,
            "messages_to_keep": messages_to_keep,
            "pre_compact_token_count": pre_compact_token_count,
            "post_compact_token_count": post_compact_token_count,
            "true_post_compact_token_count": post_compact_token_count,
        }
    except Exception as exc:  # noqa: BLE001 — parity with TS logEvent path
        log_event("tengu_sm_compact_error", {})
        if os.environ.get("USER_TYPE") == "ant":
            log_for_debugging(f"Session memory compaction error: {exc!s}")
        return None
