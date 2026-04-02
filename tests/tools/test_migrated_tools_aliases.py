"""Tests for migrated / alias tool packages."""

from __future__ import annotations

import pytest

from claude_code.tools.base import ToolUseContext
from claude_code.tools.memory_tool import MemoryTool
from claude_code.tools.parallel_tool import ParallelTool
from claude_code.tools.read_file_tool import ReadFileTool, READ_FILE_TOOL_NAME
from claude_code.tools.search_tool import SearchTool, SEARCH_TOOL_NAME
from claude_code.tools.sub_agent_tool import SubAgentTool
from claude_code.tools.task_update_tool import TaskUpdateToolDef
from claude_code.tools.write_file_tool import WriteFileTool


@pytest.mark.asyncio
async def test_read_file_tool_alias_points_at_file_read() -> None:
    from claude_code.tools.file_read_tool import FileReadTool

    assert ReadFileTool is FileReadTool
    assert READ_FILE_TOOL_NAME == "Read"


@pytest.mark.asyncio
async def test_write_file_tool_alias() -> None:
    from claude_code.tools.file_write_tool import FileWriteTool

    assert WriteFileTool is FileWriteTool


@pytest.mark.asyncio
async def test_search_tool_alias() -> None:
    from claude_code.tools.grep_tool import GrepTool

    assert SearchTool is GrepTool
    assert SEARCH_TOOL_NAME == "Grep"


@pytest.mark.asyncio
async def test_sub_agent_alias() -> None:
    from claude_code.tools.agent_tool import AgentTool

    assert SubAgentTool is AgentTool


@pytest.mark.asyncio
async def test_task_update_tool_def_execute() -> None:
    tool = TaskUpdateToolDef()
    ctx = ToolUseContext(tool_use_id="tu1")
    r = await tool.execute({"taskId": "abc", "status": "completed"}, ctx)
    assert r.success is True
    assert r.output["taskId"] == "abc"
    assert "status" in r.output["updatedFields"]

    r2 = await tool.execute({"taskId": ""}, ctx)
    assert r2.success is False


@pytest.mark.asyncio
async def test_memory_tool_write_read(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    tool = MemoryTool()
    monkeypatch.setattr(MemoryTool, "_base_dir", lambda self: str(tmp_path))

    ctx = ToolUseContext(tool_use_id="m1")
    w = await tool.execute(
        {"action": "write", "relative_path": "t.md", "content": "hello"},
        ctx,
    )
    assert w.success is True

    r = await tool.execute({"action": "read", "relative_path": "t.md"}, ctx)
    assert r.success is True
    assert r.output["content"] == "hello"

    bad = await tool.execute({"action": "read", "relative_path": "../etc/passwd"}, ctx)
    assert bad.success is False


@pytest.mark.asyncio
async def test_parallel_tool_validation() -> None:
    tool = ParallelTool()
    ctx = ToolUseContext(tool_use_id="p1")
    r = await tool.execute({"urls": []}, ctx)
    assert r.success is False
