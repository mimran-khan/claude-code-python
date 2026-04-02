"""Tests for grep_tool."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from claude_code.tools.base import ToolUseContext
from claude_code.tools.grep_tool.grep_tool import GrepTool, grep_execute, grep_get_path


def test_grep_get_path_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    p = grep_get_path({"pattern": "x"})
    assert Path(p).resolve() == tmp_path.resolve()


@pytest.mark.asyncio
async def test_grep_python_fallback_files_with_matches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("claude_code.tools.grep_tool.grep_tool.shutil.which", lambda _: None)
    (tmp_path / "one.txt").write_text("hello world\n", encoding="utf-8")
    (tmp_path / "two.txt").write_text("nope\n", encoding="utf-8")
    ctx = ToolUseContext(tool_use_id="gr1")
    res = await grep_execute(
        {"pattern": "world", "path": str(tmp_path), "output_mode": "files_with_matches"},
        ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert res.output.num_files >= 1
    assert any("one.txt" in f for f in res.output.filenames)


@pytest.mark.asyncio
async def test_grep_python_fallback_invalid_regex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("claude_code.tools.grep_tool.grep_tool.shutil.which", lambda _: None)
    ctx = ToolUseContext(tool_use_id="gr2")
    res = await grep_execute({"pattern": "(bad", "path": "."}, ctx)
    assert res.success is False
    assert "regex" in (res.error or "").lower()


@pytest.mark.asyncio
async def test_grep_requires_pattern() -> None:
    ctx = ToolUseContext(tool_use_id="gr3")
    res = await grep_execute({"pattern": "", "path": "."}, ctx)
    assert res.success is False


@pytest.mark.asyncio
async def test_grep_uses_rg_when_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("claude_code.tools.grep_tool.grep_tool.shutil.which", lambda _: "/bin/rg")
    (tmp_path / "z.txt").write_text("unique_token_xyz\n", encoding="utf-8")

    proc = MagicMock()
    proc.returncode = 0
    proc.communicate = AsyncMock(return_value=(b"z.txt\n", b""))

    async def fake_exec(*_a: object, **_kw: object) -> MagicMock:
        return proc

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)
    ctx = ToolUseContext(tool_use_id="gr4")
    res = await grep_execute(
        {"pattern": "unique", "path": str(tmp_path), "output_mode": "files_with_matches"},
        ctx,
    )
    assert res.success is True
    assert res.output.filenames
