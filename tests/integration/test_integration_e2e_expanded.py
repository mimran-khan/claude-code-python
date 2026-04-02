"""Expanded end-to-end integration tests (CLI, tools, MCP, git, config)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from claude_code.config.config import (
    get_config_path,
    get_global_config,
    get_project_config,
    set_global_config,
)
from claude_code.config.types import GlobalConfig
from claude_code.core.tool import ToolUseContext as CoreToolUseContext
from claude_code.services.mcp.client import McpClient, connect_to_server
from claude_code.services.mcp.types import McpConnection, McpStdioServerConfig
from claude_code.tools.base import ToolUseContext
from claude_code.tools.bash_tool import BashTool
from claude_code.tools.file_read_tool import FileReadTool
from claude_code.tools.file_write_tool import FileWriteTool
from claude_code.tools.glob_tool import GlobTool
from claude_code.tools.grep_tool import GrepTool
from claude_code.utils import env_utils
from claude_code.utils.git import (
    exec_git_command,
    find_canonical_git_root,
    find_git_root,
    get_head_sha,
    get_modified_files,
    get_remote_url,
    get_staged_files,
    get_untracked_files,
    git_show,
    is_shallow_clone,
)
from tests.integration.conftest import run_claude_cli

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_config_command_help_lists_edit_option() -> None:
    proc = run_claude_cli(["config", "--help"])
    assert proc.returncode == 0
    assert "--edit" in proc.stdout or "-e" in proc.stdout


def test_cli_doctor_command_help() -> None:
    proc = run_claude_cli(["doctor", "--help"])
    assert proc.returncode == 0
    assert "doctor" in proc.stdout.lower()


def test_cli_version_command_help() -> None:
    proc = run_claude_cli(["version", "--help"])
    assert proc.returncode == 0


def test_cli_unknown_subcommand_exits_with_error() -> None:
    proc = run_claude_cli(["this-subcommand-does-not-exist-xyz"])
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "command" in combined.lower() or "Usage" in combined or "No such" in combined


def test_cli_verbose_flag_before_doctor_runs() -> None:
    proc = run_claude_cli(["--verbose", "doctor"])
    assert proc.returncode == 0
    assert "QueryEngine" in proc.stdout


def test_cli_doctor_shows_python_executable_line() -> None:
    proc = run_claude_cli(["doctor"])
    assert proc.returncode == 0
    assert "executable:" in proc.stdout


def test_cli_config_shows_verbose_mode_saved_line() -> None:
    proc = run_claude_cli(["config"])
    assert proc.returncode == 0
    assert "Verbose mode" in proc.stdout


def test_cli_root_help_lists_subcommand_names() -> None:
    proc = run_claude_cli(["--help"])
    assert proc.returncode == 0
    assert "config" in proc.stdout
    assert "doctor" in proc.stdout
    assert "chat" in proc.stdout


def test_cli_chat_help_lists_prompt_short_option() -> None:
    proc = run_claude_cli(["chat", "--help"])
    assert proc.returncode == 0
    assert "-p" in proc.stdout or "--prompt" in proc.stdout


def test_cli_model_option_on_version_path() -> None:
    proc = run_claude_cli(["--model", "claude-3-5-sonnet-20241022", "--version"])
    assert proc.returncode == 0
    assert "Session ID" in proc.stdout


def test_cli_config_exists_false_when_config_missing(tmp_path: Path) -> None:
    proc = run_claude_cli(
        ["config"],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "Exists: False" in proc.stdout


def test_cli_doctor_global_config_exists_line_with_custom_dir(tmp_path: Path) -> None:
    proc = run_claude_cli(
        ["doctor"],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "Global config:" in proc.stdout
    assert "exists:" in proc.stdout.lower()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@pytest.fixture
def tool_ctx() -> ToolUseContext:
    return ToolUseContext(tool_use_id="e2e-expanded")


@pytest.mark.asyncio
async def test_bash_tool_chained_commands_with_semicolon(tmp_path: Path) -> None:
    tool = BashTool()
    ctx = CoreToolUseContext(options={"working_directory": str(tmp_path)})
    result = await tool.call(
        {"command": 'printf a && printf b && printf c'},
        ctx,
        None,
    )
    assert result.data is not None
    assert result.data.stdout == "abc"


@pytest.mark.asyncio
async def test_bash_tool_explicit_exit_zero(tmp_path: Path) -> None:
    tool = BashTool()
    ctx = CoreToolUseContext(options={"cwd": str(tmp_path)})
    result = await tool.call({"command": "exit 0"}, ctx, None)
    assert result.data is not None
    assert result.data.exit_code == 0


@pytest.mark.asyncio
async def test_file_write_multiline_preserves_newlines(
    tmp_path: Path,
    tool_ctx: ToolUseContext,
) -> None:
    target = tmp_path / "multi.txt"
    body = "line1\nline2\nline3\n"
    tool = FileWriteTool()
    res = await tool.execute({"file_path": str(target.resolve()), "content": body}, tool_ctx)
    assert res.success is True
    assert target.read_text(encoding="utf-8") == body


@pytest.mark.asyncio
async def test_file_read_resolves_relative_via_absolute_path(
    tmp_path: Path,
    tool_ctx: ToolUseContext,
) -> None:
    p = tmp_path / "abs.txt"
    p.write_text("absolute-path-read", encoding="utf-8")
    tool = FileReadTool()
    res = await tool.execute({"file_path": str(p.resolve())}, tool_ctx)
    assert res.success is True
    assert res.output is not None
    assert "absolute-path-read" in res.output.file.content


@pytest.mark.asyncio
async def test_glob_finds_hidden_file_when_pattern_matches(
    tmp_path: Path,
    tool_ctx: ToolUseContext,
) -> None:
    (tmp_path / ".envrc").write_text("x", encoding="utf-8")
    (tmp_path / "visible.txt").write_text("y", encoding="utf-8")
    tool = GlobTool()
    res = await tool.execute(
        {"pattern": ".envrc", "path": str(tmp_path.resolve())},
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert any(Path(f).name == ".envrc" for f in res.output.filenames)


@pytest.mark.asyncio
async def test_grep_head_limit_reduces_output_lines(
    tmp_path: Path,
    tool_ctx: ToolUseContext,
) -> None:
    p = tmp_path / "many.txt"
    p.write_text("\n".join(f"row {i} token" for i in range(30)) + "\n", encoding="utf-8")
    tool = GrepTool()
    res = await tool.execute(
        {
            "pattern": "token",
            "path": str(tmp_path.resolve()),
            "output_mode": "content",
            "head_limit": 5,
        },
        tool_ctx,
    )
    assert res.success is True
    assert res.output is not None
    assert res.output.content.count("\n") <= 6


@pytest.mark.asyncio
async def test_glob_py_files_recursive(tmp_path: Path, tool_ctx: ToolUseContext) -> None:
    (tmp_path / "root.py").write_text("1", encoding="utf-8")
    sub = tmp_path / "pkg"
    sub.mkdir()
    (sub / "inner.py").write_text("2", encoding="utf-8")
    tool = GlobTool()
    res = await tool.execute(
        {"pattern": "**/*.py", "path": str(tmp_path.resolve())},
        tool_ctx,
    )
    assert res.success is True
    names = {Path(f).name for f in res.output.filenames}
    assert names >= {"root.py", "inner.py"}


@pytest.mark.asyncio
async def test_bash_which_git_returns_non_empty(tmp_path: Path) -> None:
    tool = BashTool()
    ctx = CoreToolUseContext(options={"cwd": str(tmp_path)})
    result = await tool.call({"command": "command -v git || which git"}, ctx, None)
    assert result.data is not None
    assert "git" in result.data.stdout


# ---------------------------------------------------------------------------
# MCP client (stdio + resources)
# ---------------------------------------------------------------------------


def _write_fake_mcp_with_resources(path: Path) -> None:
    path.write_text(
        textwrap.dedent(
            '''
            import json
            import sys

            def reply(req_id, result):
                print(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}), flush=True)

            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                req_id = msg.get("id")
                method = msg.get("method")
                if method == "initialize" and req_id is not None:
                    reply(
                        req_id,
                        {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}, "resources": {}},
                            "serverInfo": {"name": "fake-mcp-res", "version": "0.0.1"},
                        },
                    )
                elif method == "tools/list" and req_id is not None:
                    reply(
                        req_id,
                        {
                            "tools": [
                                {
                                    "name": "noop",
                                    "description": "noop",
                                    "inputSchema": {"type": "object"},
                                }
                            ]
                        },
                    )
                elif method == "tools/call" and req_id is not None:
                    reply(req_id, {"content": [{"type": "text", "text": "called"}]})
                elif method == "resources/list" and req_id is not None:
                    reply(
                        req_id,
                        {
                            "resources": [
                                {
                                    "uri": "mem://doc",
                                    "name": "doc",
                                    "description": "integration",
                                }
                            ]
                        },
                    )
                elif method == "resources/read" and req_id is not None:
                    params = msg.get("params") or {}
                    uri = params.get("uri", "")
                    reply(
                        req_id,
                        {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "text/plain",
                                    "text": "resource-payload",
                                }
                            ]
                        },
                    )
            '''
        ).lstrip(),
        encoding="utf-8",
    )


@pytest.fixture
def fake_mcp_resources_script(tmp_path: Path) -> Path:
    p = tmp_path / "fake_mcp_res.py"
    _write_fake_mcp_with_resources(p)
    return p


@pytest.mark.asyncio
async def test_mcp_list_resources_returns_one_entry(fake_mcp_resources_script: Path) -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=[str(fake_mcp_resources_script)])
    client = await connect_to_server("res-list", cfg, scope="user")
    resources = await client.list_resources()
    assert len(resources) == 1
    assert resources[0].uri == "mem://doc"
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_read_resource_returns_payload(fake_mcp_resources_script: Path) -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=[str(fake_mcp_resources_script)])
    client = await connect_to_server("res-read", cfg, scope="user")
    raw = await client.read_resource("mem://doc")
    assert raw is not None
    assert "resource-payload" in json.dumps(raw)
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_read_resource_when_not_connected_raises() -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=["-c", "pass"])
    conn = McpConnection(name="disc", config=cfg, scope="user")
    client = McpClient(conn)
    with pytest.raises(RuntimeError, match="Not connected"):
        await client.read_resource("any://")


@pytest.mark.asyncio
async def test_mcp_call_noop_tool_on_extended_server(fake_mcp_resources_script: Path) -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=[str(fake_mcp_resources_script)])
    client = await connect_to_server("noop-call", cfg, scope="user")
    out = await client.call_tool("noop", {})
    assert out == "called"
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_connect_sets_user_scope_on_connection(fake_mcp_resources_script: Path) -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=[str(fake_mcp_resources_script)])
    client = await connect_to_server("scoped", cfg, scope="user")
    assert client.connection.scope == "user"
    await client.disconnect()


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------


def _git_init(repo: str) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "expanded@test.local"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Expanded Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def test_find_canonical_git_root_matches_find_git_root_for_simple_repo(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    a = find_git_root(str(tmp_path))
    b = find_canonical_git_root(str(tmp_path))
    assert a is not None and b is not None
    assert Path(a).resolve() == Path(b).resolve()


def test_get_head_sha_returns_40_char_hex_after_commit(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    f = tmp_path / "tracked.bin"
    f.write_text("data", encoding="utf-8")
    subprocess.run(
        ["git", "add", "tracked.bin"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "c"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    sha = get_head_sha(str(tmp_path))
    assert sha is not None
    assert len(sha) >= 7
    assert all(c in "0123456789abcdef" for c in sha.lower())


def test_get_untracked_files_lists_new_file(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    (tmp_path / "untracked.txt").write_text("u", encoding="utf-8")
    untracked = get_untracked_files(str(tmp_path))
    assert "untracked.txt" in untracked


def test_get_modified_files_lists_dirty_tracked_file(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    f = tmp_path / "t.txt"
    f.write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "add", "t.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "i"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    f.write_text("v2\n", encoding="utf-8")
    modified = get_modified_files(str(tmp_path))
    assert "t.txt" in modified


def test_get_staged_files_after_add(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    (tmp_path / "stg.txt").write_text("s", encoding="utf-8")
    subprocess.run(["git", "add", "stg.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    staged = get_staged_files(str(tmp_path))
    assert "stg.txt" in staged


def test_is_shallow_clone_false_for_normal_init(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    assert is_shallow_clone(str(tmp_path)) is False


def test_get_remote_url_none_without_origin(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    assert get_remote_url(str(tmp_path)) is None


def test_git_show_file_at_head(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    f = tmp_path / "showme.txt"
    f.write_text("snapshot\n", encoding="utf-8")
    subprocess.run(["git", "add", "showme.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "snap"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    content = git_show("HEAD", "showme.txt", cwd=str(tmp_path))
    assert content is not None
    assert "snapshot" in content


@pytest.mark.asyncio
async def test_exec_git_command_status_porcelain_empty_when_clean(tmp_path: Path) -> None:
    _git_init(str(tmp_path))
    f = tmp_path / "clean.txt"
    f.write_text("c", encoding="utf-8")
    subprocess.run(["git", "add", "clean.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "clean"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    out = await exec_git_command(["status", "--porcelain"], cwd=str(tmp_path))
    assert out.strip() == ""


# ---------------------------------------------------------------------------
# Config load / save
# ---------------------------------------------------------------------------


def test_set_global_config_release_channel_latest_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    env_utils.get_claude_config_home_dir.cache_clear()
    try:
        set_global_config(GlobalConfig(release_channel="latest", theme="dark"))
        loaded = get_global_config()
        assert loaded.release_channel == "latest"
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()


def test_set_global_config_num_startups_persisted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    env_utils.get_claude_config_home_dir.cache_clear()
    try:
        set_global_config(GlobalConfig(num_startups=99, theme="dark"))
        again = get_global_config()
        assert again.num_startups == 99
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()


def test_get_global_config_defaults_after_config_file_removed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    env_utils.get_claude_config_home_dir.cache_clear()
    try:
        set_global_config(GlobalConfig(theme="light", verbose_mode=True))
        path = Path(get_config_path())
        assert path.is_file()
        path.unlink()
        fresh = get_global_config()
        assert fresh.theme == "dark"
        assert fresh.verbose_mode is False
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()


def test_get_project_config_empty_allowed_tools_in_fresh_repo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    pc = get_project_config()
    assert pc.allowed_tools == []


def test_get_config_path_ends_with_config_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    env_utils.get_claude_config_home_dir.cache_clear()
    try:
        assert get_config_path().endswith("config.json")
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()


def test_global_config_json_contains_release_channel_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    env_utils.get_claude_config_home_dir.cache_clear()
    try:
        set_global_config(GlobalConfig(release_channel="stable"))
        raw = json.loads(Path(get_config_path()).read_text(encoding="utf-8"))
        assert raw.get("releaseChannel") == "stable"
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()
