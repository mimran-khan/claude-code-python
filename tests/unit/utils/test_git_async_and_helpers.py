"""Unit tests for ``claude_code.utils.git`` (async paths, git_exe, worktree edges)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_code.utils import git as git_mod
from claude_code.utils.git import (
    _git_run_async,
    exec_git_command,
    find_git_root,
    get_branch,
    get_default_branch_async,
    get_is_git,
    git_exe,
)


@pytest.fixture(autouse=True)
def _clear_git_caches() -> None:
    git_mod.git_exe.cache_clear()
    git_mod.find_git_root.cache_clear()
    git_mod._resolve_canonical_root.cache_clear()
    yield
    git_mod.git_exe.cache_clear()
    git_mod.find_git_root.cache_clear()
    git_mod._resolve_canonical_root.cache_clear()


@patch("claude_code.utils.git.shutil.which")
def test_git_exe_returns_resolved_path(mock_which: MagicMock) -> None:
    mock_which.return_value = "/usr/bin/git"
    assert git_exe() == "/usr/bin/git"


@patch("claude_code.utils.git.shutil.which")
def test_git_exe_falls_back_to_git_string(mock_which: MagicMock) -> None:
    mock_which.return_value = None
    assert git_exe() == "git"


@pytest.mark.asyncio
async def test_git_run_async_returns_127_when_executable_missing() -> None:
    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
        rc, out, err = await _git_run_async(["status"])
    assert rc == 127
    assert out == ""
    assert "not found" in err


@pytest.mark.asyncio
async def test_git_run_async_kills_on_timeout() -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(side_effect=TimeoutError)
    proc.kill = MagicMock()
    proc.wait = AsyncMock(return_value=0)
    proc.returncode = -1

    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        rc, out, err = await _git_run_async(["fetch"], timeout=0.01)

    proc.kill.assert_called_once()
    assert rc == 124
    assert "timed out" in err


@pytest.mark.asyncio
async def test_git_run_async_decodes_stdout_stderr() -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"h\xc3\xa9\n", b"e\xc3\xa9\n"))
    proc.returncode = 0
    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        rc, out, err = await _git_run_async(["rev-parse", "HEAD"], timeout=None)
    assert rc == 0
    assert "é" in out
    assert "é" in err


@pytest.mark.asyncio
async def test_get_is_git_true_when_git_prints_true() -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"true\n", b""))
    proc.returncode = 0
    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        assert await get_is_git("/repo") is True


@pytest.mark.asyncio
async def test_get_is_git_false_on_nonzero_rc() -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"true\n", b""))
    proc.returncode = 1
    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        assert await get_is_git() is False


@pytest.mark.asyncio
async def test_get_branch_returns_main_when_git_fails() -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"", b""))
    proc.returncode = 1
    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        assert await get_branch() == "main"


@pytest.mark.asyncio
async def test_get_branch_maps_detached_head_to_main() -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"HEAD\n", b""))
    proc.returncode = 0
    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        assert await get_branch() == "main"


@pytest.mark.asyncio
async def test_get_branch_returns_feature_name() -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"feature/x\n", b""))
    proc.returncode = 0
    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        assert await get_branch() == "feature/x"


@pytest.mark.asyncio
async def test_exec_git_command_returns_stdout_on_success() -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"out\n", b""))
    proc.returncode = 0
    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        assert await exec_git_command(["log", "-1"]) == "out\n"


@pytest.mark.asyncio
async def test_exec_git_command_returns_empty_on_error() -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"hidden\n", b"err"))
    proc.returncode = 1
    with patch("claude_code.utils.git.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        assert await exec_git_command(["invalid"]) == ""


@pytest.mark.asyncio
async def test_get_default_branch_async_calls_to_thread() -> None:
    with patch("claude_code.utils.git.asyncio.to_thread", new=AsyncMock(return_value="develop")) as tt:
        out = await get_default_branch_async("/p")
    tt.assert_awaited_once()
    assert out == "develop"


def test_find_git_root_accepts_git_file_not_directory(tmp_path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    (repo / ".git").write_text("gitdir: ../.git/modules/x\n", encoding="utf-8")
    assert find_git_root(str(repo)) == str(repo.resolve())


def test_find_git_root_skips_level_when_git_check_raises(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    with patch("claude_code.utils.git.os.path.isdir", side_effect=OSError("stat")):
        assert find_git_root(str(tmp_path)) is None


def test_resolve_canonical_root_returns_same_when_dot_git_is_directory(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    assert git_mod._resolve_canonical_root(str(repo.resolve())) == str(repo.resolve())


def test_resolve_canonical_root_invalid_gitdir_line_returns_root(tmp_path) -> None:
    repo = tmp_path / "wt"
    repo.mkdir()
    (repo / ".git").write_text("not-gitdir: foo\n", encoding="utf-8")
    assert git_mod._resolve_canonical_root(str(repo.resolve())) == str(repo.resolve())


def test_resolve_canonical_root_submodule_without_commondir_returns_root(tmp_path) -> None:
    repo = tmp_path / "sub"
    repo.mkdir()
    wt_git = tmp_path / "gits" / "abc"
    wt_git.mkdir(parents=True)
    (repo / ".git").write_text(f"gitdir: {wt_git}\n", encoding="utf-8")
    assert git_mod._resolve_canonical_root(str(repo.resolve())) == str(repo.resolve())
