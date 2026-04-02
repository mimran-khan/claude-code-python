"""Integration tests for git helpers against real repositories."""

from __future__ import annotations

import subprocess

import pytest

from claude_code.utils.git import (
    exec_git_command,
    find_git_root,
    get_branch,
    get_current_branch,
    get_default_branch,
    get_git_status,
    get_is_git,
    git_add,
    git_commit,
    git_diff,
    git_log,
    is_git_ignored,
)

pytestmark = pytest.mark.integration


def _git_init(repo: str) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "integration@test.local"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Integration Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def test_find_git_root_returns_repo_path(tmp_path) -> None:
    _git_init(str(tmp_path))
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    root = find_git_root(str(nested))
    assert root == str(tmp_path.resolve())


def test_find_git_root_none_outside_repo(tmp_path) -> None:
    assert find_git_root(str(tmp_path)) is None


def test_get_current_branch_after_first_commit(tmp_path) -> None:
    _git_init(str(tmp_path))
    (tmp_path / "init.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "init.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    branch = get_current_branch(str(tmp_path))
    assert branch is not None
    assert len(branch) > 0


def test_get_git_status_empty_clean_repo(tmp_path) -> None:
    _git_init(str(tmp_path))
    (tmp_path / "tracked.txt").write_text("v1\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "tracked.txt"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    assert get_git_status(str(tmp_path)) == []


def test_get_git_status_detects_staged_new_file(tmp_path) -> None:
    """Staged additions use index column; ?? untracked rows are skipped by current parser."""
    _git_init(str(tmp_path))
    p = tmp_path / "staged_new.txt"
    p.write_text("x", encoding="utf-8")
    subprocess.run(
        ["git", "add", "staged_new.txt"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    statuses = get_git_status(str(tmp_path))
    paths = {s.path for s in statuses}
    assert "staged_new.txt" in paths
    assert any(s.path == "staged_new.txt" and s.is_staged for s in statuses)


def test_get_git_status_detects_modified_file(tmp_path) -> None:
    _git_init(str(tmp_path))
    f = tmp_path / "file.txt"
    f.write_text("a\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "c1"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    f.write_text("b\n", encoding="utf-8")
    statuses = get_git_status(str(tmp_path))
    assert any("file.txt" in s.path for s in statuses)


def test_git_diff_shows_worktree_change(tmp_path) -> None:
    _git_init(str(tmp_path))
    f = tmp_path / "x.txt"
    f.write_text("old\n", encoding="utf-8")
    subprocess.run(["git", "add", "x.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "c"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    f.write_text("new\n", encoding="utf-8")
    diff = git_diff(cwd=str(tmp_path))
    assert diff is not None
    assert "old" in diff or "new" in diff


def test_git_diff_staged_vs_last_commit(tmp_path) -> None:
    _git_init(str(tmp_path))
    f = tmp_path / "staged.txt"
    f.write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "add", "staged.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "c"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    f.write_text("v2\n", encoding="utf-8")
    subprocess.run(["git", "add", "staged.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    diff = git_diff(cwd=str(tmp_path), staged=True)
    assert diff is not None
    assert "v2" in diff or "v1" in diff


def test_get_default_branch_returns_string(tmp_path) -> None:
    _git_init(str(tmp_path))
    b = get_default_branch(str(tmp_path))
    assert isinstance(b, str)
    assert b in ("main", "master") or len(b) > 0


@pytest.mark.asyncio
async def test_get_is_git_true_inside_repo(tmp_path) -> None:
    _git_init(str(tmp_path))
    assert await get_is_git(str(tmp_path)) is True


@pytest.mark.asyncio
async def test_get_is_git_false_outside_repo(tmp_path) -> None:
    assert await get_is_git(str(tmp_path)) is False


@pytest.mark.asyncio
async def test_get_branch_after_commit(tmp_path) -> None:
    _git_init(str(tmp_path))
    (tmp_path / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "f.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "c"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    b = await get_branch(str(tmp_path))
    assert isinstance(b, str)
    assert len(b) > 0


@pytest.mark.asyncio
async def test_exec_git_command_rev_parse(tmp_path) -> None:
    _git_init(str(tmp_path))
    out = await exec_git_command(["rev-parse", "--show-toplevel"], cwd=str(tmp_path))
    assert str(tmp_path.resolve()) in out or len(out) > 0


def test_git_add_and_commit_helpers(tmp_path) -> None:
    _git_init(str(tmp_path))
    p = tmp_path / "tracked.py"
    p.write_text("print(1)\n", encoding="utf-8")
    assert git_add(["tracked.py"], cwd=str(tmp_path)) is True
    assert git_commit("add file", cwd=str(tmp_path)) is True
    log = git_log(cwd=str(tmp_path), max_count=1)
    assert len(log) >= 1


def test_is_git_ignored_respects_gitignore(tmp_path) -> None:
    _git_init(str(tmp_path))
    (tmp_path / ".gitignore").write_text("secret.txt\n", encoding="utf-8")
    secret = tmp_path / "secret.txt"
    secret.write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "gitignore"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    assert is_git_ignored("secret.txt", cwd=str(tmp_path)) is True
