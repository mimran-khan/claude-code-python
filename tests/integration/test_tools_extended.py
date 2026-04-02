"""Extra tool integration tests (filesystem, shell, grep edge cases)."""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_code.core.tool import ToolUseContext as CoreToolUseContext
from claude_code.tools.base import ToolUseContext
from claude_code.tools.bash_tool import BashTool
from claude_code.tools.file_read_tool import FileReadTool
from claude_code.tools.file_write_tool import FileWriteTool
from claude_code.tools.glob_tool import GlobTool
from claude_code.tools.grep_tool import GrepTool

pytestmark = pytest.mark.integration


@pytest.fixture
def tool_ctx() -> ToolUseContext:
    return ToolUseContext(tool_use_id="integration-extended")


@pytest.mark.asyncio
async def test_file_read_missing_file_returns_error(
    tmp_path: Path,
    tool_ctx: ToolUseContext,
) -> None:
    missing = tmp_path / "nope.txt"
    tool = FileReadTool()
    res = await tool.execute({"file_path": str(missing.resolve())}, tool_ctx)
    assert res.success is False
    assert res.error is not None
    assert "not found" in res.error.lower() or "File not found" in res.error


@pytest.mark.asyncio
async def test_file_read_empty_file_succeeds(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    p = tmp_path / "empty.txt"
    p.write_text("", encoding="utf-8")
    tool = FileReadTool()
    res = await tool.execute({"file_path": str(p.resolve())}, tool_ctx)
    assert res.success is True
    assert res.output is not None


@pytest.mark.asyncio
async def test_file_write_overwrites_existing(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    p = tmp_path / "w.txt"
    p.write_text("old", encoding="utf-8")
    read_tool = FileReadTool()
    pre = await read_tool.execute({"file_path": str(p.resolve())}, tool_ctx)
    assert pre.success is True
    tool = FileWriteTool()
    res = await tool.execute({"file_path": str(p.resolve()), "content": "new"}, tool_ctx)
    assert res.success is True
    assert p.read_text(encoding="utf-8") == "new"


@pytest.mark.asyncio
async def test_file_read_with_explicit_utf8_encoding(
    tmp_path: Path,
    tool_ctx: ToolUseContext,
) -> None:
    p = tmp_path / "enc.txt"
    p.write_text("hello world\n" * 20 + "café\n", encoding="utf-8")
    tool = FileReadTool()
    res = await tool.execute(
        {"file_path": str(p.resolve()), "encoding": "utf-8"},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert "café" in res.output.file.content


@pytest.mark.asyncio
async def test_file_read_limit_one_line(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    p = tmp_path / "multi.txt"
    p.write_text("L1\nL2\nL3\n", encoding="utf-8")
    tool = FileReadTool()
    res = await tool.execute(
        {"file_path": str(p.resolve()), "offset": 1, "limit": 1},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert "L1" in res.output.file.content
    assert "L2" not in res.output.file.content


@pytest.mark.asyncio
async def test_grep_rejects_nonexistent_path(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    tool = GrepTool()
    res = await tool.execute(
        {
            "pattern": "x",
            "path": str((tmp_path / "missing_dir").resolve()),
            "output_mode": "content",
        },
        tool_ctx,
    )
    assert res.success is False


@pytest.mark.asyncio
async def test_grep_count_mode_reports_matches(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    (tmp_path / "c1.txt").write_text("foo\nfoo\n", encoding="utf-8")
    tool = GrepTool()
    res = await tool.execute(
        {
            "pattern": "foo",
            "path": str(tmp_path.resolve()),
            "output_mode": "count",
            "head_limit": 50,
        },
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert res.output.mode == "count"
    assert res.output.num_matches is not None
    assert res.output.num_matches >= 1


@pytest.mark.asyncio
async def test_grep_content_with_line_numbers_flag(
    tmp_path: Path,
    tool_ctx: ToolUseContext,
) -> None:
    p = tmp_path / "numbered.py"
    p.write_text("alpha = 1\nbeta = 2\n", encoding="utf-8")
    tool = GrepTool()
    res = await tool.execute(
        {
            "pattern": "beta",
            "path": str(tmp_path.resolve()),
            "output_mode": "content",
            "-n": True,
            "head_limit": 20,
        },
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert "beta" in res.output.content


@pytest.mark.asyncio
async def test_grep_invalid_regex_returns_error_python_fallback(
    tmp_path: Path, tool_ctx: ToolUseContext
) -> None:
    """Invalid pattern fails in Python fallback path (no rg) or rg error path."""
    (tmp_path / "t.txt").write_text("text\n", encoding="utf-8")
    tool = GrepTool()
    res = await tool.execute(
        {
            "pattern": "[",
            "path": str(tmp_path.resolve()),
            "output_mode": "content",
            "head_limit": 5,
        },
        tool_ctx,
    )
    assert res.success is False
    assert res.error is not None


@pytest.mark.asyncio
async def test_glob_respects_path_argument(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    sub = tmp_path / "onlyhere"
    sub.mkdir()
    (sub / "keep.md").write_text("x", encoding="utf-8")
    (tmp_path / "root.md").write_text("y", encoding="utf-8")
    tool = GlobTool()
    res = await tool.execute(
        {"pattern": "*.md", "path": str(sub.resolve())},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    names = {Path(p).name for p in res.output.filenames}
    assert "keep.md" in names
    assert "root.md" not in names


@pytest.mark.asyncio
async def test_glob_single_file_pattern(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    (tmp_path / "exact.name").write_text("z", encoding="utf-8")
    tool = GlobTool()
    res = await tool.execute(
        {"pattern": "exact.name", "path": str(tmp_path.resolve())},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert any(Path(p).name == "exact.name" for p in res.output.filenames)


@pytest.mark.asyncio
async def test_bash_pwd_reflects_working_directory(tmp_path: Path) -> None:
    tool = BashTool()
    ctx = CoreToolUseContext(options={"working_directory": str(tmp_path)})
    result = await tool.call({"command": "pwd"}, ctx, None)
    assert result.data is not None
    assert str(tmp_path.resolve()) in result.data.stdout.replace("\n", "")


@pytest.mark.asyncio
async def test_bash_env_var_inline(tmp_path: Path) -> None:
    tool = BashTool()
    ctx = CoreToolUseContext(options={"working_directory": str(tmp_path)})
    result = await tool.call(
        {"command": 'export CC_ITEST=42 && printf "%s" "$CC_ITEST"'},
        ctx,
        None,
    )
    assert result.data is not None
    assert "42" in result.data.stdout


@pytest.mark.asyncio
async def test_bash_stderr_captured_on_failure(tmp_path: Path) -> None:
    tool = BashTool()
    ctx = CoreToolUseContext(options={"working_directory": str(tmp_path)})
    result = await tool.call({"command": "ls /nonexistent_path_cc_12345 2>&1 || true"}, ctx, None)
    assert result.data is not None
    assert len(result.data.stdout + result.data.stderr) > 0


@pytest.mark.asyncio
async def test_file_write_unicode_content_roundtrip(
    tmp_path: Path,
    tool_ctx: ToolUseContext,
) -> None:
    target = tmp_path / "uni.txt"
    tool = FileWriteTool()
    text = "你好 €"
    res = await tool.execute({"file_path": str(target.resolve()), "content": text}, tool_ctx)
    assert res.success is True
    assert target.read_text(encoding="utf-8") == text


@pytest.mark.asyncio
async def test_grep_multiline_false_default_matches_single_line(
    tmp_path: Path, tool_ctx: ToolUseContext
) -> None:
    p = tmp_path / "ml.txt"
    p.write_text("start\nend\n", encoding="utf-8")
    tool = GrepTool()
    res = await tool.execute(
        {
            "pattern": "start",
            "path": str(tmp_path.resolve()),
            "output_mode": "content",
            "head_limit": 10,
        },
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert "start" in res.output.content
