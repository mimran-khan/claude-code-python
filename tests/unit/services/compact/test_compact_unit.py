"""Unit tests for ``claude_code.services.compact`` modules."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from claude_code.services.compact import micro_compact
from claude_code.services.compact.compact import (
    CompactConfig,
    CompactResult,
    compact_messages,
    should_compact,
)
from claude_code.services.compact.grouping import group_messages_by_api_round
from claude_code.services.compact.token_utils import (
    estimate_message_tokens,
    estimate_messages_tokens,
    estimate_text_tokens,
    message_to_text,
)


def test_compact_config_trigger_fallback() -> None:
    cfg = CompactConfig(max_tokens=50, compact_trigger_tokens=None)
    assert cfg.compact_trigger_tokens is None


def test_should_compact_false_below_trigger() -> None:
    cfg = CompactConfig(max_tokens=100, min_messages_to_keep=2)
    assert should_compact([1, 2, 3], cfg, current_tokens=50) is False


def test_should_compact_false_when_too_few_messages() -> None:
    cfg = CompactConfig(max_tokens=10, min_messages_to_keep=4)
    assert should_compact([1, 2, 3, 4], cfg, current_tokens=999) is False


def test_should_compact_true_when_over_trigger_and_enough_messages() -> None:
    cfg = CompactConfig(max_tokens=10, min_messages_to_keep=2, compact_trigger_tokens=5)
    assert should_compact([1, 2, 3, 4, 5], cfg, current_tokens=10) is True


@pytest.mark.asyncio
async def test_compact_messages_noop_when_not_needed() -> None:
    cfg = CompactConfig(max_tokens=10_000, min_messages_to_keep=2)
    msgs = [{"role": "user", "content": "a"}, {"role": "user", "content": "b"}]
    result = await compact_messages(msgs, cfg, current_tokens=5)
    assert result.compacted is False
    assert result.messages_before == 2
    assert result.messages_after == 2


@pytest.mark.asyncio
async def test_compact_messages_reduces_history() -> None:
    cfg = CompactConfig(
        max_tokens=1,
        min_messages_to_keep=2,
        compact_trigger_tokens=0,
        summary_max_chars=5000,
    )
    msgs = [{"role": "user", "content": f"m{i}"} for i in range(6)]
    result = await compact_messages(msgs, cfg, current_tokens=100)
    assert result.compacted is True
    assert result.messages_before == 6
    assert result.summary
    assert result.messages is not None
    assert len(result.messages) < len(msgs)


@pytest.mark.asyncio
async def test_compact_messages_prepends_user_instruction_prefix() -> None:
    cfg = CompactConfig(
        max_tokens=1,
        min_messages_to_keep=1,
        compact_trigger_tokens=0,
        summary_max_chars=8000,
        user_instruction_prefix=" focus on tests ",
    )
    msgs = [{"role": "user", "content": "x"}, {"role": "user", "content": "y"}]
    result = await compact_messages(msgs, cfg, current_tokens=50)
    assert result.compacted is True
    assert result.summary is not None
    assert "User compaction instructions" in result.summary


def test_message_to_text_variants() -> None:
    assert message_to_text(None) == ""
    assert message_to_text("plain") == "plain"
    assert message_to_text({"content": "c"}) == "c"
    assert message_to_text({"content": [{"type": "text", "text": "t"}]}) == "t"
    assert "tool" in message_to_text({"content": [{"type": "tool_result", "content": "tool"}]})


def test_estimate_text_tokens_empty() -> None:
    assert estimate_text_tokens("") == 0


def test_estimate_text_tokens_heuristic_without_tiktoken() -> None:
    with patch("claude_code.services.compact.token_utils._tiktoken_encoding", return_value=None):
        assert estimate_text_tokens("abcd") == 1


def test_estimate_messages_tokens_sum() -> None:
    with patch("claude_code.services.compact.token_utils._tiktoken_encoding", return_value=None):
        a = estimate_messages_tokens([{"content": "aaaa"}, {"content": "bbbb"}])
        assert a == estimate_message_tokens({"content": "aaaa"}) + estimate_message_tokens({"content": "bbbb"})


class _Msg:
    def __init__(self, mtype: str, mid: str | None = None) -> None:
        self.type = mtype
        self.message = _Pay(mid) if mid is not None else None


class _Pay:
    def __init__(self, mid: str) -> None:
        self.id = mid


def test_group_messages_by_api_round_splits_on_new_assistant_id() -> None:
    m1 = _Msg("assistant", "a1")
    m2 = _Msg("user")
    m3 = _Msg("assistant", "a2")
    groups = group_messages_by_api_round([m1, m2, m3])
    assert len(groups) == 2
    assert groups[0] == [m1, m2]
    assert groups[1] == [m3]


def test_group_messages_by_api_round_single_group() -> None:
    u = _Msg("user")
    groups = group_messages_by_api_round([u])
    assert groups == [[u]]


@pytest.mark.asyncio
async def test_run_micro_compact_disabled_env_returns_same() -> None:
    with patch.dict("os.environ", {"CLAUDE_CODE_DISABLE_MICROCOMPACT": "true"}):
        msgs: list[dict[str, object]] = [{"type": "user", "message": {"content": "hi"}}]
        out = await micro_compact.run_micro_compact(msgs, None, "q")
    assert out.messages == msgs
    assert out.compaction_info is None


@pytest.mark.asyncio
async def test_run_micro_compact_truncates_large_user_string() -> None:
    with patch.dict("os.environ", {"CLAUDE_CODE_DISABLE_MICROCOMPACT": ""}):
        big = "x" * 60000
        msgs = [{"type": "user", "message": {"content": big}}]
        out = await micro_compact.run_micro_compact(msgs, None, "q")
    assert out.compaction_info is not None
    assert out.compaction_info.tokens_freed > 0
    new_content = out.messages[0]["message"]["content"]
    assert isinstance(new_content, str)
    assert len(new_content) < len(big)


@pytest.mark.asyncio
async def test_run_micro_compact_truncates_large_tool_result_block() -> None:
    with patch.dict("os.environ", {"CLAUDE_CODE_DISABLE_MICROCOMPACT": ""}):
        big = "z" * 120_000
        msgs = [
            {
                "type": "user",
                "message": {"content": [{"type": "tool_result", "content": big}]},
            }
        ]
        out = await micro_compact.run_micro_compact(msgs, None, "q")
    assert out.compaction_info is not None
    block = out.messages[0]["message"]["content"][0]
    assert len(block["content"]) < len(big)


def test_compaction_info_dataclass() -> None:
    info = micro_compact.CompactionInfo(tokens_freed=3, messages_modified=1)
    assert info.tokens_freed == 3


def test_compact_result_dataclass_fields() -> None:
    r = CompactResult(
        compacted=False,
        messages_before=1,
        messages_after=1,
        tokens_before=2,
        tokens_after=2,
    )
    assert r.summary is None


def test_reset_microcompact_state_noop() -> None:
    assert micro_compact.reset_microcompact_state() is None
