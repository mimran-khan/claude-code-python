"""Tests for export_command/ui and brief_ui (TS migration)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_code.bootstrap import state as state_mod
from claude_code.commands.brief_ui import call as brief_call
from claude_code.commands.export_command.ui import (
    call as export_call,
)
from claude_code.commands.export_command.ui import (
    extract_first_prompt,
    format_timestamp,
    render_messages_to_plain_text,
    sanitize_filename,
)


def test_sanitize_filename_strips_special_chars() -> None:
    assert sanitize_filename("Hello World!") == "hello-world"


def test_extract_first_prompt_string_content() -> None:
    messages = [
        {"type": "user", "message": {"content": "first line\nsecond"}},
    ]
    assert extract_first_prompt(messages) == "first line"


def test_extract_first_prompt_array_text_block() -> None:
    messages = [
        {
            "type": "user",
            "message": {"content": [{"type": "text", "text": "  hi there  "}]},
        },
    ]
    assert extract_first_prompt(messages) == "hi there"


def test_format_timestamp_padding() -> None:
    dt = __import__("datetime").datetime(2026, 4, 2, 1, 2, 3)
    assert format_timestamp(dt) == "2026-04-02-010203"


def test_render_messages_to_plain_text_basic() -> None:
    messages = [
        {"type": "user", "message": {"content": "a"}},
        {"type": "assistant", "message": {"content": "b"}},
    ]
    out = render_messages_to_plain_text(messages, [])
    assert "User" in out and "a" in out
    assert "Assistant" in out and "b" in out


@pytest.mark.asyncio
async def test_export_call_writes_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    ctx = MagicMock()
    ctx.messages = [{"type": "user", "message": {"content": "x"}}]
    ctx.options = MagicMock(tools=[])
    out = await export_call("out", context=ctx)
    assert "exported to" in out["value"]
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "--- User ---\nx"


@pytest.mark.asyncio
async def test_export_call_no_args_returns_dialog_payload() -> None:
    ctx = MagicMock()
    ctx.messages = []
    ctx.options = MagicMock(tools=[])
    out = await export_call("", context=ctx)
    assert out["type"] == "export_dialog"
    assert "defaultFilename" in out


@pytest.mark.asyncio
async def test_brief_call_toggles_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    state_mod.set_user_msg_opt_in(False)
    with (
        patch("claude_code.commands.brief_ui.is_brief_entitled", return_value=True),
        patch("claude_code.commands.brief_ui.log_event"),
    ):
        out = await brief_call("", context=None)
    assert "enabled" in out["message"].lower()
    assert state_mod.get_user_msg_opt_in() is True
    state_mod.set_user_msg_opt_in(False)
