"""Additional unit tests for claude_code.utils.git (mocked subprocess / filesystem)."""

from __future__ import annotations

import asyncio
import os
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_code.utils import git as git_mod
from claude_code.utils.git import (
    _git_run_async,
    find_canonical_git_root,
    find_git_root,
    get_current_branch,
    get_default_branch,
    get_git_status,
    get_head_sha,
    get_remote_url,
    git_add,
    git_commit,
    is_git_ignored,
    is_shallow_clone,
)


@pytest.fixture(autouse=True)
def clear_git_caches() -> None:
    git_mod.git_exe.cache_clear()
    git_mod.find_git_root.cache_clear()
    git_mod._resolve_canonical_root.cache_clear()
    yield
    git_mod.git_exe.cache_clear()
    git_mod.find_git_root.cache_clear()
    git_mod._resolve_canonical_root.cache_clear()


def test_find_git_root_detects_dot_git_dir(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    assert find_git_root(str(repo)) == str(repo.resolve())


def test_find_git_root_returns_none_without_git(tmp_path) -> None:
    assert find_git_root(str(tmp_path)) is None


def test_find_canonical_git_root_matches_find_git_root_for_plain_repo(tmp_path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    (repo / ".git").mkdir()
    root = str(repo.resolve())
    assert find_canonical_git_root(str(repo / "nested")) == root


@patch("claude_code.utils.git.subprocess.run")
def test_get_current_branch_returns_name(mock_run) -> None:
    mock_run.return_value = CompletedProcess(["git"], 0, "main\n", "")
    assert get_current_branch("/repo") == "main"
    mock_run.assert_called_once()


@patch("claude_code.utils.git.subprocess.run")
def test_get_current_branch_detached_returns_none(mock_run) -> None:
    mock_run.return_value = CompletedProcess(["git"], 0, "HEAD\n", "")
    assert get_current_branch() is None


@patch("claude_code.utils.git.subprocess.run")
def test_get_default_branch_from_origin_head(mock_run) -> None:
    mock_run.return_value = CompletedProcess(["git"], 0, "origin/develop\n", "")
    assert get_default_branch() == "develop"


@patch("claude_code.utils.git.subprocess.run")
def test_get_head_sha_success(mock_run) -> None:
    mock_run.return_value = CompletedProcess(["git"], 0, "abc123\n", "")
    assert get_head_sha() == "abc123"


@patch("claude_code.utils.git.subprocess.run")
def test_get_remote_url_success(mock_run) -> None:
    mock_run.return_value = CompletedProcess(["git"], 0, "git@github.com:a/b.git\n", "")
    assert get_remote_url(remote="origin") == "git@github.com:a/b.git"


@patch("claude_code.utils.git.os.path.exists")
@patch("claude_code.utils.git.find_git_root")
def test_is_shallow_clone_true_when_shallow_file(mock_find_root, mock_exists) -> None:
    mock_find_root.return_value = "/r"
    def exists_side(p: str) -> bool:
        return p.endswith(os.path.join(".git", "shallow"))

    mock_exists.side_effect = exists_side
    assert is_shallow_clone() is True


@patch("claude_code.utils.git.subprocess.run")
def test_get_git_status_parses_porcelain(mock_run) -> None:
    # M + space: modified in index (staged), clean in worktree
    mock_run.return_value = CompletedProcess(["git"], 0, "M  staged.txt\0?? u.txt\0", "")
    statuses = get_git_status()
    assert any(s.path == "staged.txt" and s.is_staged for s in statuses)
    assert any(s.path == "u.txt" and s.status == "?" for s in statuses)


@patch("claude_code.utils.git.subprocess.run")
def test_get_git_status_returns_empty_on_error(mock_run) -> None:
    mock_run.side_effect = CalledProcessError(1, "git")
    assert get_git_status() == []


@patch("claude_code.utils.git.subprocess.run")
def test_is_git_ignored_true_when_check_ignore_zero(mock_run) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    assert is_git_ignored("node_modules") is True


@patch("claude_code.utils.git.log_error")
@patch("claude_code.utils.git.subprocess.run")
def test_git_add_returns_false_on_failure(mock_run, mock_log) -> None:
    mock_run.side_effect = RuntimeError("fail")
    assert git_add(["x.py"], cwd="/r") is False


@patch("claude_code.utils.git.log_error")
@patch("claude_code.utils.git.subprocess.run")
def test_git_commit_returns_false_on_failure(mock_run, mock_log) -> None:
    mock_run.side_effect = RuntimeError("fail")
    assert git_commit("msg", cwd="/r") is False


@pytest.mark.asyncio
@patch("claude_code.utils.git.asyncio.create_subprocess_exec", new_callable=AsyncMock)
async def test_git_run_async_file_not_found(mock_cpe) -> None:
    mock_cpe.side_effect = FileNotFoundError()
    rc, out, err = await _git_run_async(["status"], cwd="/tmp")
    assert rc == 127
    assert out == ""
    assert "not found" in err


@pytest.mark.asyncio
@patch("claude_code.utils.git.asyncio.create_subprocess_exec", new_callable=AsyncMock)
async def test_git_run_async_timeout(mock_cpe) -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock()
    proc.kill = MagicMock()
    proc.wait = AsyncMock()
    mock_cpe.return_value = proc

    async def fake_wait_for(aw: object, timeout: float | None = None) -> None:
        # Avoid "coroutine was never awaited" when simulating wait_for timeout.
        if asyncio.iscoroutine(aw):
            aw.close()
        raise TimeoutError

    with patch("claude_code.utils.git.asyncio.wait_for", side_effect=fake_wait_for):
        rc, out, err = await _git_run_async(["fetch"], cwd="/tmp", timeout=1.0)
    assert rc == 124
    proc.kill.assert_called_once()
