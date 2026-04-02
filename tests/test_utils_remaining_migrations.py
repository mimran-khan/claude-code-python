"""Tests for newly migrated small utils modules."""

from __future__ import annotations

import os
from unittest.mock import patch

from pydantic import BaseModel

from claude_code.utils.auto_mode_denials import (
    AutoModeDenial,
    clear_auto_mode_denials_for_tests,
    get_auto_mode_denials,
    record_auto_mode_denial,
)
from claude_code.utils.circular_buffer import CircularBuffer
from claude_code.utils.content_array import insert_block_after_tool_results
from claude_code.utils.command_lifecycle import (
    notify_command_lifecycle,
    set_command_lifecycle_listener,
)
from claude_code.utils.extra_usage import is_billed_as_extra_usage
from claude_code.utils.get_worktree_paths_portable import (
    get_worktree_paths_portable_sync,
)
from claude_code.utils.immediate_command import should_inference_config_command_be_immediate
from claude_code.utils.ink import to_ink_color
from claude_code.utils.model.model import (
    get_model_strings,
    get_public_model_display_name,
    render_model_name,
)
from claude_code.utils.session_env_vars import (
    clear_session_env_vars,
    delete_session_env_var,
    get_session_env_vars,
    set_session_env_var,
)
from claude_code.utils.standalone_agent import get_standalone_agent_name
from claude_code.utils.stream import Stream
from claude_code.utils.user_prompt_keywords import (
    matches_keep_going_keyword,
    matches_negative_keyword,
)
from claude_code.utils.words import generate_short_word_slug, generate_word_slug
from claude_code.utils.zod_to_json_schema import (
    clear_zod_to_json_schema_cache_for_tests,
    zod_to_json_schema,
)


def test_command_lifecycle_listener() -> None:
    seen: list[tuple[str, str]] = []

    def cb(uuid: str, state: str) -> None:
        seen.append((uuid, state))

    set_command_lifecycle_listener(cb)
    notify_command_lifecycle("u1", "started")
    notify_command_lifecycle("u1", "completed")
    set_command_lifecycle_listener(None)
    notify_command_lifecycle("u2", "started")
    assert seen == [("u1", "started"), ("u1", "completed")]


def test_session_env_vars_roundtrip() -> None:
    clear_session_env_vars()
    set_session_env_var("FOO", "bar")
    assert dict(get_session_env_vars()) == {"FOO": "bar"}
    delete_session_env_var("FOO")
    assert "FOO" not in get_session_env_vars()
    clear_session_env_vars()


def test_auto_mode_denials_cap() -> None:
    clear_auto_mode_denials_for_tests()
    for i in range(25):
        record_auto_mode_denial(
            AutoModeDenial("t", "d", "r", float(i)),
        )
    assert len(get_auto_mode_denials()) == 20
    clear_auto_mode_denials_for_tests()


@patch.dict("os.environ", {"USER_TYPE": "ant"}, clear=False)
def test_immediate_command_ant_user() -> None:
    assert should_inference_config_command_be_immediate() is True


def test_user_prompt_keywords() -> None:
    assert matches_negative_keyword("This is horrible") is True
    assert matches_negative_keyword("Hello world") is False
    assert matches_keep_going_keyword("continue") is True
    assert matches_keep_going_keyword("please keep going now") is True


def test_ink_color_known_and_fallback() -> None:
    assert "SUBAGENTS" in to_ink_color("cyan")
    assert to_ink_color(None).startswith("cyan")
    assert to_ink_color("not-a-theme").startswith("ansi:")


def test_standalone_agent_name() -> None:
    class _Ctx:
        name = "solo"

    class _State:
        standalone_agent_context = _Ctx()

    with patch("claude_code.utils.standalone_agent.get_team_name", return_value=None):
        assert get_standalone_agent_name(_State()) == "solo"
    with patch("claude_code.utils.standalone_agent.get_team_name", return_value="t"):
        assert get_standalone_agent_name(_State()) is None


def test_zod_to_json_schema_pydantic() -> None:
    clear_zod_to_json_schema_cache_for_tests()

    class M(BaseModel):
        x: int

    s1 = zod_to_json_schema(M)
    s2 = zod_to_json_schema(M)
    assert s1 == s2
    assert s1.get("properties", {}).get("x")
    clear_zod_to_json_schema_cache_for_tests()


def test_insert_block_after_tool_results_appends_continuation() -> None:
    content: list[object] = [{"type": "tool_result", "tool_use_id": "1", "content": []}]
    insert_block_after_tool_results(content, {"type": "text", "text": "directive"})
    assert len(content) == 3
    assert content[1] == {"type": "text", "text": "directive"}
    assert content[2] == {"type": "text", "text": "."}


def test_insert_block_after_tool_results_before_last_without_tool_result() -> None:
    content: list[object] = [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]
    insert_block_after_tool_results(content, {"type": "x"})
    assert content == [{"type": "text", "text": "a"}, {"type": "x"}, {"type": "text", "text": "b"}]


def test_get_public_model_display_name_known_models() -> None:
    ms = get_model_strings()
    assert get_public_model_display_name(ms["opus46"]) == "Opus 4.6"
    assert get_public_model_display_name(ms["opus46"] + "[1m]") == "Opus 4.6 (1M context)"
    assert get_public_model_display_name("not-a-catalog-model") is None


def test_render_model_name_public_and_fallback() -> None:
    ms = get_model_strings()
    assert render_model_name(ms["sonnet46"]) == "Sonnet 4.6"
    assert render_model_name("internal-unknown-id") == "internal-unknown-id"


@patch.dict(os.environ, {"USER_TYPE": "ant"}, clear=False)
@patch("claude_code.utils.effort._resolve_ant_model")
def test_render_model_name_ant_with_ant_model(mock_ant: object) -> None:
    mock_ant.return_value = {"model": "capybara-v2-fast"}
    assert render_model_name("x") == "cap*****-v2-fast"


def test_words_slug_format() -> None:
    slug = generate_word_slug()
    parts = slug.split("-")
    assert len(parts) == 3
    short = generate_short_word_slug()
    assert len(short.split("-")) == 2


@patch("claude_code.utils.extra_usage.is_claude_ai_subscriber", return_value=False)
def test_extra_usage_not_subscriber(_mock: object) -> None:
    assert is_billed_as_extra_usage("opus[1m]", False, False) is False


@patch("claude_code.utils.extra_usage.is_claude_ai_subscriber", return_value=True)
def test_extra_usage_fast_mode(_mock: object) -> None:
    assert is_billed_as_extra_usage("opus[1m]", True, False) is True


def test_get_worktree_paths_portable_in_git_repo() -> None:
    paths = get_worktree_paths_portable_sync("/Users/imrankha/Downloads/ClaudeCodeLeaked")
    assert isinstance(paths, list)
    if paths:
        assert all(isinstance(p, str) for p in paths)


def test_circular_buffer_order_and_cap() -> None:
    buf: CircularBuffer[int] = CircularBuffer(3)
    buf.add(1)
    buf.add(2)
    buf.add(3)
    buf.add(4)
    assert buf.to_array() == [2, 3, 4]
    assert buf.get_recent(2) == [3, 4]
    buf.clear()
    assert buf.length() == 0


async def test_stream_enqueue_done() -> None:
    s: Stream[int] = Stream()
    s.enqueue(1)
    s.enqueue(2)
    s.done()
    out: list[int] = []
    async for x in s:
        out.append(x)
    assert out == [1, 2]


async def test_get_worktree_paths_portable_async() -> None:
    from claude_code.utils.get_worktree_paths_portable import get_worktree_paths_portable

    paths = await get_worktree_paths_portable("/Users/imrankha/Downloads/ClaudeCodeLeaked")
    assert isinstance(paths, list)
