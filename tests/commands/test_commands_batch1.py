"""Tests for migrated commands batch (add-dir, branch, manifest, bridge-kick)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from claude_code.commands.add_dir.validation import (
    AddDirectoryEmptyPath,
    AddDirectorySuccess,
    add_dir_help_message,
    all_working_directories,
    validate_directory_for_workspace,
)
from claude_code.commands.branch.branch_logic import derive_first_prompt
from claude_code.commands.bridge_kick import bridge_kick_call
from claude_code.commands.commands_manifest import (
    built_in_command_specs,
    find_command,
    internal_only_specs,
)
from claude_code.commands.protocols import (
    register_bridge_debug_handle,
)
from claude_code.core.tool import ToolPermissionContext


@pytest.mark.asyncio
async def test_validate_empty_path() -> None:
    ctx = ToolPermissionContext()
    r = await validate_directory_for_workspace("", ctx)
    assert isinstance(r, AddDirectoryEmptyPath)


@pytest.mark.asyncio
async def test_validate_success_tmp(tmp_path) -> None:
    ctx = ToolPermissionContext()
    (tmp_path / "proj").mkdir()
    d = tmp_path / "w"
    d.mkdir()
    r = await validate_directory_for_workspace(str(d), ctx, cwd=str(tmp_path / "proj"))
    assert isinstance(r, AddDirectorySuccess)
    assert r.absolute_path == os.path.abspath(str(d))


def test_all_working_directories_includes_additional() -> None:
    from claude_code.core.tool import AdditionalWorkingDirectory

    ctx = ToolPermissionContext(
        additional_working_directories={
            "x": AdditionalWorkingDirectory(path="/extra"),
        }
    )
    dirs = all_working_directories(ctx, cwd="/project")
    assert os.path.abspath("/project") in dirs
    assert any("extra" in p for p in dirs)


def test_derive_first_prompt() -> None:
    assert derive_first_prompt(None) == "Branched conversation"
    msg = {
        "type": "user",
        "message": {"content": "hello\nworld"},
    }
    assert derive_first_prompt(msg) == "hello world"


@pytest.mark.asyncio
async def test_bridge_kick_no_handle() -> None:
    register_bridge_debug_handle(None)
    out = await bridge_kick_call("")
    assert "No bridge debug handle" in out["value"]


class _FakeHandle:
    def __init__(self) -> None:
        self.closed: list[int] = []

    def fire_close(self, code: int) -> None:
        self.closed.append(code)

    def inject_fault(self, fault: dict) -> None:
        pass

    def wake_poll_loop(self) -> None:
        pass

    def force_reconnect(self) -> None:
        pass

    def describe(self) -> str:
        return "ok"


@pytest.mark.asyncio
async def test_bridge_kick_close() -> None:
    h = _FakeHandle()
    register_bridge_debug_handle(h)
    out = await bridge_kick_call("close 1002")
    assert "1002" in out["value"]
    assert h.closed == [1002]
    register_bridge_debug_handle(None)


def test_find_command() -> None:
    specs = list(built_in_command_specs())
    c = find_command("clear", specs)
    assert c is not None
    assert c.name == "clear"


def test_internal_only_specs() -> None:
    assert len(internal_only_specs()) == 3


def test_add_dir_help_message_success() -> None:
    msg = add_dir_help_message(AddDirectorySuccess(absolute_path="/tmp/x"))
    assert "/tmp/x" in msg


@pytest.mark.asyncio
async def test_compact_call_empty_messages_raises() -> None:
    from claude_code.commands.compact.compact_impl import call as compact_call

    with pytest.raises(RuntimeError, match="No messages"):
        await compact_call("", messages=[])


@pytest.mark.asyncio
async def test_compact_call_returns_stub_shape() -> None:
    from claude_code.commands.compact.compact_impl import call as compact_call

    out = await compact_call("summarize tests", messages=[{"role": "user"}])
    assert out["type"] == "compact"
    assert out.get("compactionResult", {}).get("stub") is True


@pytest.mark.asyncio
async def test_rename_call_blocks_teammate() -> None:
    from claude_code.commands.rename.rename_impl import call as rename_call

    seen: list[tuple[str, dict]] = []

    def on_done(msg: str, meta: dict) -> None:
        seen.append((msg, meta))

    with patch(
        "claude_code.commands.rename.rename_impl.is_in_process_teammate",
        return_value=True,
    ):
        await rename_call(on_done, object(), "x")
    assert seen and "teammate" in seen[0][0].lower()


@pytest.mark.asyncio
async def test_rename_call_explicit_name() -> None:
    from claude_code.commands.rename.rename_impl import call as rename_call

    seen: list[str] = []

    def on_done(msg: str, _meta: dict) -> None:
        seen.append(msg)

    with patch(
        "claude_code.commands.rename.rename_impl.is_in_process_teammate",
        return_value=False,
    ):
        await rename_call(on_done, object(), "  my-session  ")
    assert any("my-session" in s for s in seen)
