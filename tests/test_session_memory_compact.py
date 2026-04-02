"""Tests for session memory compaction helpers (sessionMemoryCompact.ts)."""

from __future__ import annotations

import pytest

from claude_code.services.compact.session_memory_compact import (
    SessionMemoryCompactConfig,
    adjust_index_to_preserve_api_invariants,
    calculate_messages_to_keep_index,
    has_text_blocks,
    reset_session_memory_compact_config,
    set_session_memory_compact_config,
)


@pytest.fixture(autouse=True)
def _reset_cfg() -> None:
    reset_session_memory_compact_config()
    yield
    reset_session_memory_compact_config()


def test_has_text_blocks_assistant_with_text() -> None:
    msg = {
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": "hi"}]},
    }
    assert has_text_blocks(msg) is True


def test_has_text_blocks_user_string() -> None:
    msg = {"type": "user", "message": {"content": "hello"}}
    assert has_text_blocks(msg) is True


def test_calculate_messages_to_keep_index_respects_min_messages() -> None:
    set_session_memory_compact_config(
        SessionMemoryCompactConfig(min_tokens=1, min_text_block_messages=3, max_tokens=100_000)
    )
    messages = [
        {"type": "user", "uuid": "a", "message": {"content": "x"}},
        {"type": "user", "uuid": "b", "message": {"content": "y"}},
        {"type": "user", "uuid": "c", "message": {"content": "z"}},
    ]
    idx = calculate_messages_to_keep_index(messages, last_summarized_index=-1)
    assert idx == 0


def test_adjust_index_preserves_tool_pair() -> None:
    messages = [
        {
            "type": "assistant",
            "message": {
                "content": [{"type": "tool_use", "id": "tu1", "name": "x", "input": {}}]
            },
        },
        {
            "type": "user",
            "message": {
                "content": [{"type": "tool_result", "tool_use_id": "tu1", "content": "ok"}]
            },
        },
    ]
    adjusted = adjust_index_to_preserve_api_invariants(messages, start_index=1)
    assert adjusted == 0
