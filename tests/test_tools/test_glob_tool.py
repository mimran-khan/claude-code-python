"""Tests for glob_tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_code.tools.base import ToolUseContext
from claude_code.tools.glob_tool.glob_tool import GlobTool, glob_execute, glob_tool_get_path


def test_glob_tool_get_path_defaults_to_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    assert Path(glob_tool_get_path({"pattern": "*"})).resolve() == tmp_path.resolve()


@pytest.mark.asyncio
async def test_glob_execute_finds_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("1", encoding="utf-8")
    (tmp_path / "b.txt").write_text("2", encoding="utf-8")
    (tmp_path / "c.py").write_text("3", encoding="utf-8")
    ctx = ToolUseContext(tool_use_id="g1")
    res = await glob_execute({"pattern": "*.txt", "path": str(tmp_path)}, ctx)
    assert res.success is True
    assert res.output is not None
    names = sorted(Path(p).name for p in res.output.filenames)
    assert names == ["a.txt", "b.txt"]


@pytest.mark.asyncio
async def test_glob_execute_requires_pattern() -> None:
    ctx = ToolUseContext(tool_use_id="g2")
    res = await glob_execute({"pattern": ""}, ctx)
    assert res.success is False


@pytest.mark.asyncio
async def test_validate_input_rejects_file_path(tmp_path: Path) -> None:
    fp = tmp_path / "notadir.txt"
    fp.write_text("x", encoding="utf-8")
    tool = GlobTool()
    ctx = ToolUseContext(tool_use_id="g3")
    out = await tool.validate_input({"pattern": "*", "path": str(fp)}, ctx)
    assert out["result"] is False


@pytest.mark.asyncio
async def test_validate_input_missing_dir(tmp_path: Path) -> None:
    tool = GlobTool()
    ctx = ToolUseContext(tool_use_id="g4")
    out = await tool.validate_input(
        {"pattern": "*", "path": str(tmp_path / "missing_dir")},
        ctx,
    )
    assert out["result"] is False
