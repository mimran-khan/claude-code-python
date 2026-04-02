"""Tests for file_read_tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_code.tools.base import ToolUseContext
from claude_code.tools.file_read_tool import FILE_READ_TOOL_NAME, FileReadTool, read_file
from claude_code.tools.file_read_tool.file_read_tool import BLOCKED_DEVICE_PATHS, MaxFileReadTokenExceededError


@pytest.mark.asyncio
async def test_file_read_tool_name_and_schema() -> None:
    tool = FileReadTool()
    assert tool.name == FILE_READ_TOOL_NAME
    schema = tool.get_input_schema()
    assert "file_path" in schema["properties"]
    assert schema["required"] == ["file_path"]


@pytest.mark.asyncio
async def test_validate_input_blocks_device_path() -> None:
    tool = FileReadTool()
    ctx = ToolUseContext(tool_use_id="t1")
    for dev in list(BLOCKED_DEVICE_PATHS)[:3]:
        out = await tool.validate_input({"file_path": dev}, ctx)
        assert out["result"] is False


@pytest.mark.asyncio
async def test_validate_input_requires_path() -> None:
    tool = FileReadTool()
    ctx = ToolUseContext(tool_use_id="t1")
    out = await tool.validate_input({"file_path": ""}, ctx)
    assert out["result"] is False


@pytest.mark.asyncio
async def test_read_text_file_success(tmp_path: Path) -> None:
    fp = tmp_path / "sample.txt"
    fp.write_text("line1\nline2\nline3\n", encoding="utf-8")
    ctx = ToolUseContext(tool_use_id="r1")
    res = await read_file({"file_path": str(fp)}, ctx)
    assert res.success is True
    assert res.output is not None
    assert "line1" in str(res.output)


@pytest.mark.asyncio
async def test_read_file_offset_limit(tmp_path: Path) -> None:
    fp = tmp_path / "n.txt"
    fp.write_text("a\nb\nc\nd\n", encoding="utf-8")
    ctx = ToolUseContext(tool_use_id="r2")
    res = await read_file({"file_path": str(fp), "offset": 2, "limit": 2}, ctx)
    assert res.success is True
    assert any(v.get("is_partial_view") for v in ctx.read_file_state.values())


@pytest.mark.asyncio
async def test_read_missing_file() -> None:
    ctx = ToolUseContext(tool_use_id="r3")
    res = await read_file({"file_path": "/nonexistent/path/zzzz.txt"}, ctx)
    assert res.success is False
    assert res.error_code == 1


@pytest.mark.asyncio
async def test_pages_rejected_for_non_pdf(tmp_path: Path) -> None:
    fp = tmp_path / "x.txt"
    fp.write_text("hi", encoding="utf-8")
    ctx = ToolUseContext(tool_use_id="r4")
    res = await read_file({"file_path": str(fp), "pages": "1-2"}, ctx)
    assert res.success is False
    assert "pdf" in (res.error or "").lower()


def test_max_file_read_token_exceeded_error_message() -> None:
    err = MaxFileReadTokenExceededError(100, 50)
    assert "100" in str(err) and "50" in str(err)
