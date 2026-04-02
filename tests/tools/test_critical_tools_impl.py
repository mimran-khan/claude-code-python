"""Smoke tests for bash, file read/write, glob, and grep tool implementations."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from claude_code.tools.bash_tool import execute_bash
from claude_code.tools.base import ToolUseContext
from claude_code.tools.file_read_tool.file_read_tool import read_file
from claude_code.tools.file_write_tool.file_write_tool import write_file
from claude_code.tools.glob_tool.glob_tool import glob_execute
from claude_code.tools.grep_tool.grep_tool import grep_execute


@pytest.mark.asyncio
async def test_execute_bash_echo() -> None:
    r = await execute_bash("echo hello")
    assert r.data.stdout.strip() == "hello"
    assert r.data.exit_code == 0
    assert not r.data.interrupted


@pytest.mark.asyncio
async def test_execute_bash_timeout_kills() -> None:
    r = await execute_bash({"command": "sleep 10", "timeout": 100})
    assert r.data.interrupted
    assert r.data.exit_code == 124


@pytest.mark.asyncio
async def test_read_write_glob_grep_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        fp = p / "sub" / "sample.txt"
        ctx = ToolUseContext(tool_use_id="t1")
        w = await write_file(
            {"file_path": str(fp), "content": "alpha\nbeta\ngamma\n"},
            ctx,
        )
        assert w.success

        rd = await read_file(
            {"file_path": str(fp), "offset": 2, "limit": 1},
            ctx,
        )
        assert rd.success
        assert rd.output is not None
        assert "beta" in str(rd.output)

        g = await glob_execute({"pattern": "*.txt", "path": str(p / "sub")}, ctx)
        assert g.success
        assert g.output is not None
        assert any(str(fp) == x or x.endswith("sample.txt") for x in g.output.filenames)

        gr = await grep_execute({"pattern": r"beta", "path": str(p)}, ctx)
        assert gr.success
        assert gr.output is not None
        assert gr.output.mode in ("content", "files_with_matches")


@pytest.mark.asyncio
async def test_read_file_rejects_binary_text_mode() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fp = os.path.join(tmp, "bin.dat")
        with open(fp, "wb") as f:
            f.write(b"\x00\x01\x02\xff")
        ctx = ToolUseContext(tool_use_id="t2")
        r = await read_file({"file_path": fp}, ctx)
        assert not r.success
        assert r.error_code == 8
