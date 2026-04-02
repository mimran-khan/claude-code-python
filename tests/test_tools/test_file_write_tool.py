"""Tests for file_write_tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_code.utils.path_utils import expand_path
from claude_code.tools.base import ToolUseContext
from claude_code.tools.file_write_tool.file_write_tool import FileWriteTool, write_file


@pytest.mark.asyncio
async def test_write_creates_new_file(tmp_path: Path) -> None:
    fp = tmp_path / "new.txt"
    ctx = ToolUseContext(tool_use_id="w1")
    res = await write_file({"file_path": str(fp), "content": "created"}, ctx)
    assert res.success is True
    assert res.output is not None
    assert res.output.type == "create"
    assert fp.read_text(encoding="utf-8") == "created"


@pytest.mark.asyncio
async def test_write_updates_after_full_read(tmp_path: Path) -> None:
    fp = tmp_path / "exist.txt"
    fp.write_text("old", encoding="utf-8")
    ctx = ToolUseContext(tool_use_id="w2")
    # Simulate full read state (timestamp must match file mtime logic in validate)
    import os

    mtime_ms = float(int(os.path.getmtime(str(fp)) * 1000))
    ctx.read_file_state[expand_path(str(fp))] = {
        "content": "old",
        "timestamp": mtime_ms,
        "offset": None,
        "limit": None,
    }
    tool = FileWriteTool()
    v = await tool.validate_input({"file_path": str(fp), "content": "x"}, ctx)
    assert v["result"] is True
    res = await write_file({"file_path": str(fp), "content": "new"}, ctx)
    assert res.success is True
    assert res.output.type == "update"
    assert fp.read_text(encoding="utf-8") == "new"


@pytest.mark.asyncio
async def test_validate_rejects_when_file_not_read_yet(tmp_path: Path) -> None:
    fp = tmp_path / "only_on_disk.txt"
    fp.write_text("x", encoding="utf-8")
    tool = FileWriteTool()
    ctx = ToolUseContext(tool_use_id="w3")
    v = await tool.validate_input({"file_path": str(fp), "content": "y"}, ctx)
    assert v["result"] is False
    assert "read" in v["message"].lower()


@pytest.mark.asyncio
async def test_file_write_tool_execute_dispatches(tmp_path: Path) -> None:
    fp = tmp_path / "via_execute.txt"
    tool = FileWriteTool()
    ctx = ToolUseContext(tool_use_id="w4")
    res = await tool.execute({"file_path": str(fp), "content": "z"}, ctx)
    assert res.success is True
