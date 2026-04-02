"""Tests for recently wired stub implementations (MCP, slash commands, mentions, plugins)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_code.core.tool import ValidationResult
from claude_code.entrypoints.mcp_launcher import create_claude_code_mcp_server
from claude_code.plugins.loader import PluginLoader
from claude_code.tools.shared.spawn_multi_agent import SpawnTeammateConfig, spawn_teammate
from claude_code.utils.process_input.process_input import ProcessUserInputContext, process_user_input
from claude_code.utils.process_input.process_text import process_text_prompt


@pytest.mark.asyncio
async def test_process_user_input_slash_help() -> None:
    ctx = ProcessUserInputContext(cwd=".")
    result = await process_user_input("/help", ctx)
    assert result.result_text is not None
    assert "Available commands" in result.result_text


@pytest.mark.asyncio
async def test_process_text_expands_file_mention(tmp_path: Path) -> None:
    f = tmp_path / "note.txt"
    f.write_text("hello-mention", encoding="utf-8")

    class _Ctx:
        cwd = str(tmp_path)

    out = await process_text_prompt("See @note.txt for details", _Ctx())
    assert out["messages"]
    text = out["messages"][0]["content"][0]["text"]
    assert "hello-mention" in text


def test_create_claude_code_mcp_server_builds_server() -> None:
    """Avoid loading the full tool registry (some tool packages are still split)."""
    fake_tool = MagicMock()
    fake_tool.name = "StubTool"
    fake_tool.description = "stub"
    fake_tool.input_schema = {"type": "object", "properties": {}}
    fake_tool.validate_input = MagicMock(return_value=ValidationResult(result=True))
    out = MagicMock()
    out.data = {"ok": True}
    fake_tool.call = AsyncMock(return_value=out)

    with patch("claude_code.entrypoints.mcp_launcher.get_tools", return_value=[fake_tool]):
        server = create_claude_code_mcp_server(cwd=".")
    assert server.name == "claude-code-python"


@pytest.mark.asyncio
async def test_plugin_loader_mounts_sys_path(tmp_path: Path) -> None:
    plug_dir = tmp_path / "demo-plugin"
    plug_dir.mkdir()
    (plug_dir / "plugin.json").write_text(
        '{"name": "demo", "version": "1.0.0", "type": "skills"}',
        encoding="utf-8",
    )
    loader = PluginLoader(plugins_dir=tmp_path)
    loader.discover()
    info = loader.get("demo-plugin")
    assert info is not None
    await loader.load("demo-plugin")
    root = str(plug_dir.resolve())
    assert root in sys.path
    unloaded = await loader.unload("demo-plugin")
    assert unloaded is True
    assert "demo-plugin" not in loader._plugin_sys_path_entries


@pytest.mark.asyncio
async def test_spawn_teammate_returns_without_env_cmd() -> None:
    cfg = SpawnTeammateConfig(name="t1", prompt="do work")
    out = await spawn_teammate(cfg, None)
    assert out.name == "t1"
    assert out.teammate_id
    assert out.agent_id
