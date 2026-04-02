"""Unit tests for claude_code.services.compact.compact."""

from __future__ import annotations

import pytest

from claude_code.services.compact.compact import (
    CompactConfig,
    CompactResult,
    _build_summary_prefix,
    _prepend_compact_user_message,
    compact_messages,
    should_compact,
)


def test_should_compact_false_when_under_trigger() -> None:
    cfg = CompactConfig(max_tokens=100, min_messages_to_keep=2)
    msgs = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    assert should_compact(msgs, cfg, current_tokens=50) is False


def test_should_compact_false_when_too_few_messages() -> None:
    cfg = CompactConfig(max_tokens=10, min_messages_to_keep=4)
    msgs = [{"role": "user", "content": "x"}]
    assert should_compact(msgs, cfg, current_tokens=999) is False


def test_should_compact_true_when_over_trigger_and_enough_messages() -> None:
    cfg = CompactConfig(max_tokens=100, min_messages_to_keep=2)
    msgs = [
        {"role": "user", "content": str(i)} for i in range(5)
    ]
    assert should_compact(msgs, cfg, current_tokens=150) is True


def test_should_compact_uses_explicit_trigger() -> None:
    cfg = CompactConfig(max_tokens=500, compact_trigger_tokens=50, min_messages_to_keep=2)
    msgs = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}, {"role": "user", "content": "c"}]
    assert should_compact(msgs, cfg, current_tokens=60) is True
    assert should_compact(msgs, cfg, current_tokens=40) is False


def test_build_summary_prefix_truncates_long_messages() -> None:
    long_text = "x" * 900
    older = [{"role": "user", "content": long_text}]
    s = _build_summary_prefix(older, max_chars=50_000)
    assert "Compacted earlier" in s
    assert "…" in s or len(s) < len(long_text) + 200


def test_prepend_compact_user_message_plain_dict_tail() -> None:
    tail = [{"role": "assistant", "content": "tail"}]
    out = _prepend_compact_user_message("summary", tail)
    assert out[0]["role"] == "user"
    assert out[0]["content"] == "summary"
    assert out[1] == tail[0]


def test_prepend_compact_user_message_typed_tail_shape() -> None:
    tail = [{"type": "user", "message": {"role": "user", "content": "x"}}]
    out = _prepend_compact_user_message("sum", tail)
    assert out[0]["type"] == "user"
    assert out[0]["message"]["content"] == "sum"


def test_prepend_compact_empty_tail() -> None:
    assert _prepend_compact_user_message("only", []) == [
        {"role": "user", "content": "only"},
    ]


@pytest.mark.asyncio
async def test_compact_messages_noop_when_not_needed() -> None:
    cfg = CompactConfig(max_tokens=10_000, min_messages_to_keep=2)
    msgs = [{"role": "user", "content": "hi"}]
    res = await compact_messages(msgs, cfg, current_tokens=100)
    assert res.compacted is False
    assert res.messages_before == res.messages_after == 1
    assert res.messages == msgs


@pytest.mark.asyncio
async def test_compact_messages_reduces_message_count() -> None:
    cfg = CompactConfig(
        max_tokens=50,
        min_messages_to_keep=2,
        target_tokens=500_000,
        summary_max_chars=20_000,
    )
    msgs = [{"role": "user", "content": f"msg-{i}"} for i in range(10)]
    res = await compact_messages(msgs, cfg, current_tokens=100)
    assert res.compacted is True
    assert res.messages_before == 10
    assert res.messages_after < 10
    assert res.summary is not None
    assert res.messages is not None
    assert res.messages[0]["role"] == "user"


@pytest.mark.asyncio
async def test_compact_result_dataclass_fields() -> None:
    r = CompactResult(
        compacted=False,
        messages_before=1,
        messages_after=1,
        tokens_before=10,
        tokens_after=10,
        messages=[],
    )
    assert r.compacted is False
