"""MCP config parsing, config persistence edge cases, and extra git helpers."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

from claude_code.config.config import get_config_path, get_global_config, set_global_config
from claude_code.config.types import GlobalConfig
from claude_code.services.mcp.client import McpClient, connect_to_server
from claude_code.services.mcp.types import (
    McpConnection,
    McpStdioServerConfig,
    parse_server_config,
)
from claude_code.utils import env_utils
from claude_code.utils.git import git_exe, git_log
from claude_code.utils.settings.constants import reset_enabled_setting_sources
from claude_code.utils.settings.settings import reset_settings_cache

pytestmark = pytest.mark.integration


def _git_init(repo: str) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "e2e@test.local"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "E2E"],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def test_parse_server_config_sse_includes_headers() -> None:
    cfg = parse_server_config(
        {
            "type": "sse",
            "url": "http://example/sse",
            "headers": {"Authorization": "Bearer x"},
        }
    )
    assert cfg.type == "sse"
    assert cfg.url == "http://example/sse"
    assert cfg.headers == {"Authorization": "Bearer x"}


def test_parse_server_config_http_includes_headers_helper() -> None:
    cfg = parse_server_config(
        {
            "type": "http",
            "url": "http://h/mcp",
            "headersHelper": "fn",
        }
    )
    assert cfg.type == "http"
    assert getattr(cfg, "headers_helper", None) == "fn"


def test_parse_server_config_ws_includes_headers() -> None:
    cfg = parse_server_config(
        {"type": "ws", "url": "ws://host/ws", "headers": {"X": "1"}},
    )
    assert cfg.type == "ws"
    assert cfg.headers == {"X": "1"}


def test_parse_server_config_stdio_empty_command_allowed() -> None:
    cfg = parse_server_config({"type": "stdio", "command": "", "args": []})
    assert isinstance(cfg, McpStdioServerConfig)
    assert cfg.command == ""


def test_parse_server_config_unknown_type_falls_back_to_stdio() -> None:
    cfg = parse_server_config({"type": "not-a-real-transport", "url": "x"})
    assert isinstance(cfg, McpStdioServerConfig)


def test_parse_server_config_sdk_empty_name() -> None:
    cfg = parse_server_config({"type": "sdk"})
    assert cfg.type == "sdk"
    assert cfg.name == ""


@pytest.mark.asyncio
async def test_mcp_stdio_connect_fails_when_server_exits_immediately() -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=["-c", "import sys; sys.exit(0)"])
    conn = McpConnection(name="die", config=cfg, scope="user")
    client = McpClient(conn)
    ok = await client.connect()
    assert ok is False
    assert client.connection.status == "error"


@pytest.mark.asyncio
async def test_mcp_connect_to_server_disconnects_cleanly_on_failure() -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=["-c", "raise SystemExit(1)"])
    client = await connect_to_server("failfast", cfg, scope="user")
    assert client.connection.status in ("error", "disconnected")
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_call_tool_when_never_connected_raises() -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=["-c", "pass"])
    conn = McpConnection(name="nc", config=cfg, scope="user")
    client = McpClient(conn)
    with pytest.raises(RuntimeError, match="Not connected"):
        await client.call_tool("any", {})


@pytest.fixture
def isolated_config_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Path, None, None]:
    reset_settings_cache()
    reset_enabled_setting_sources()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    env_utils.get_claude_config_home_dir.cache_clear()
    yield tmp_path
    env_utils.get_claude_config_home_dir.cache_clear()
    reset_settings_cache()
    reset_enabled_setting_sources()


def test_get_global_config_invalid_json_file_uses_defaults(isolated_config_home: Path) -> None:
    (isolated_config_home / "config.json").write_text("{not json", encoding="utf-8")
    gc = get_global_config()
    assert gc.theme == "dark"
    assert isinstance(gc.verbose_mode, bool)


def test_get_global_config_empty_json_object_uses_defaults(isolated_config_home: Path) -> None:
    (isolated_config_home / "config.json").write_text("{}", encoding="utf-8")
    gc = get_global_config()
    assert gc.theme == "dark"


def test_set_and_reload_global_config_theme(isolated_config_home: Path) -> None:
    set_global_config(GlobalConfig(theme="light", verbose_mode=False, num_startups=0))
    path = get_config_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data.get("theme") == "light"
    again = get_global_config()
    assert again.theme == "light"


def test_get_config_path_under_custom_dir(isolated_config_home: Path) -> None:
    p = get_config_path()
    assert p.endswith("config.json")
    assert str(isolated_config_home.resolve()) in p


def test_git_exe_returns_non_empty_string() -> None:
    exe = git_exe()
    assert isinstance(exe, str)
    assert len(exe) > 0


def test_git_log_returns_multiple_commits(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    (tmp_path / "a.txt").write_text("1", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "c1"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    (tmp_path / "b.txt").write_text("2", encoding="utf-8")
    subprocess.run(["git", "add", "b.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "c2"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    entries = git_log(cwd=str(tmp_path), max_count=5)
    assert len(entries) >= 2


def test_git_log_filtered_by_path(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    (tmp_path / "tracked.log").write_text("x", encoding="utf-8")
    subprocess.run(
        ["git", "add", "tracked.log"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "log commit"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    lines = git_log(path="tracked.log", cwd=str(tmp_path), max_count=3)
    assert len(lines) >= 1
