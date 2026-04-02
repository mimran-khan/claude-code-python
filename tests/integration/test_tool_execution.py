"""
Integration tests for core tools against a real filesystem and shell.

Uses the migrated tool implementations under claude_code.tools.*_tool (wired stack).
"""

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
    return ToolUseContext(tool_use_id="integration-test")


@pytest.mark.asyncio
async def test_bash_tool_executes_echo(tool_ctx: ToolUseContext) -> None:
    tool = BashTool()
    ctx = CoreToolUseContext()
    result = await tool.call(
        {"command": 'printf "hello-integration"'},
        ctx,
        None,
    )
    assert result.data is not None
    assert "hello-integration" in result.data.stdout


@pytest.mark.asyncio
async def test_bash_tool_respects_working_directory(tmp_path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "marker.txt").write_text("inside", encoding="utf-8")
    tool = BashTool()
    ctx = CoreToolUseContext(options={"working_directory": str(sub)})
    result = await tool.call(
        {"command": "test -f marker.txt && printf ok"},
        ctx,
        None,
    )
    assert result.data is not None
    assert result.data.stdout.strip() == "ok"


@pytest.mark.asyncio
async def test_bash_tool_python_version_stdout(tool_ctx: ToolUseContext) -> None:
    tool = BashTool()
    ctx = CoreToolUseContext()
    result = await tool.call({"command": "python3 -c \"print(2+2)\""}, ctx, None)
    assert result.data is not None
    assert "4" in result.data.stdout


@pytest.mark.asyncio
async def test_file_read_tool_reads_text_file(tmp_path, tool_ctx: ToolUseContext) -> None:
    p = tmp_path / "sample.txt"
    p.write_text("line one\nline two\n", encoding="utf-8")
    tool = FileReadTool()
    res = await tool.execute(
        {"file_path": str(p.resolve())},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert "line one" in res.output.file.content
    assert "line two" in res.output.file.content


@pytest.mark.asyncio
async def test_file_read_tool_offset_and_limit(tmp_path, tool_ctx: ToolUseContext) -> None:
    p = tmp_path / "lines.txt"
    p.write_text("a\nb\nc\nd\n", encoding="utf-8")
    tool = FileReadTool()
    res = await tool.execute(
        {"file_path": str(p.resolve()), "offset": 2, "limit": 2},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert "b" in res.output.file.content
    assert "c" in res.output.file.content
    assert "a" not in res.output.file.content


@pytest.mark.asyncio
async def test_file_write_tool_creates_new_file(tmp_path, tool_ctx: ToolUseContext) -> None:
    target = tmp_path / "new.txt"
    tool = FileWriteTool()
    res = await tool.execute(
        {
            "file_path": str(target.resolve()),
            "content": "fresh content",
        },
        tool_ctx,
    )
    assert res.success is True
    assert target.read_text(encoding="utf-8") == "fresh content"


@pytest.mark.asyncio
async def test_file_write_tool_creates_nested_path(tmp_path, tool_ctx: ToolUseContext) -> None:
    target = tmp_path / "nested" / "dir" / "out.txt"
    tool = FileWriteTool()
    res = await tool.execute(
        {"file_path": str(target.resolve()), "content": "x"},
        tool_ctx,
    )
    assert res.success is True
    assert target.is_file()


@pytest.mark.asyncio
async def test_glob_tool_finds_matching_files(tmp_path, tool_ctx: ToolUseContext) -> None:
    (tmp_path / "a.txt").write_text("1", encoding="utf-8")
    (tmp_path / "b.txt").write_text("2", encoding="utf-8")
    (tmp_path / "c.py").write_text("3", encoding="utf-8")
    tool = GlobTool()
    res = await tool.execute(
        {"pattern": "*.txt", "path": str(tmp_path.resolve())},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    names = {Path(p).name for p in res.output.filenames}
    assert names == {"a.txt", "b.txt"}


@pytest.mark.asyncio
async def test_glob_tool_returns_empty_when_no_matches(tmp_path, tool_ctx: ToolUseContext) -> None:
    tool = GlobTool()
    res = await tool.execute(
        {"pattern": "*.nomatch", "path": str(tmp_path.resolve())},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert res.output.filenames == []


@pytest.mark.asyncio
async def test_grep_tool_content_mode_finds_line(tmp_path, tool_ctx: ToolUseContext) -> None:
    p = tmp_path / "src.py"
    p.write_text("def unique_marker_xyzzy():\n    return 1\n", encoding="utf-8")
    tool = GrepTool()
    res = await tool.execute(
        {
            "pattern": "unique_marker_xyzzy",
            "path": str(tmp_path.resolve()),
            "output_mode": "content",
            "head_limit": 50,
        },
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert "unique_marker_xyzzy" in res.output.content


@pytest.mark.asyncio
async def test_grep_tool_files_with_matches(tmp_path, tool_ctx: ToolUseContext) -> None:
    (tmp_path / "one.py").write_text("foo = 1\n", encoding="utf-8")
    (tmp_path / "two.py").write_text("foo = 2\n", encoding="utf-8")
    tool = GrepTool()
    res = await tool.execute(
        {
            "pattern": "foo",
            "path": str(tmp_path.resolve()),
            "output_mode": "files_with_matches",
            "head_limit": 20,
        },
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert res.output.num_files >= 1


@pytest.mark.asyncio
async def test_grep_tool_case_insensitive(tmp_path, tool_ctx: ToolUseContext) -> None:
    p = tmp_path / "t.py"
    p.write_text("UPPERCASE_TOKEN\n", encoding="utf-8")
    tool = GrepTool()
    res = await tool.execute(
        {
            "pattern": "uppercase_token",
            "path": str(tmp_path.resolve()),
            "output_mode": "content",
            "-i": True,
            "head_limit": 10,
        },
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert "UPPERCASE_TOKEN" in res.output.content


@pytest.mark.asyncio
async def test_bash_nonzero_exit_code(tmp_path: Path) -> None:
    tool = BashTool()
    ctx = CoreToolUseContext(options={"cwd": str(tmp_path)})
    result = await tool.call({"command": "exit 42"}, ctx, None)
    assert result.data is not None
    assert result.data.exit_code == 42


@pytest.mark.asyncio
async def test_glob_nested_pattern(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    (tmp_path / "root.txt").write_text("a", encoding="utf-8")
    sub = tmp_path / "nested"
    sub.mkdir()
    (sub / "inner.txt").write_text("b", encoding="utf-8")
    tool = GlobTool()
    res = await tool.execute(
        {"pattern": "**/*.txt", "path": str(tmp_path.resolve())},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    names = {Path(p).name for p in res.output.filenames}
    assert "root.txt" in names and "inner.txt" in names


@pytest.mark.asyncio
async def test_grep_empty_pattern_rejected(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    tool = GrepTool()
    res = await tool.execute(
        {"pattern": "", "path": str(tmp_path.resolve()), "output_mode": "content"},
        tool_ctx,
    )
    assert res.success is False
