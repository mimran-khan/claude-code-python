"""Git helpers: repo discovery, status, diffs, and async subprocess wrappers.

Most synchronous helpers use :mod:`subprocess` and return empty or ``None`` on
failure. Async helpers use :func:`asyncio.create_subprocess_exec` with
``GIT_TERMINAL_PROMPT=0`` for non-interactive use.

Migrated from: ``utils/git.ts`` (927 lines).
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from functools import lru_cache
from typing import NamedTuple

from .log import log_error


@lru_cache(maxsize=1)
def git_exe() -> str:
    """Resolve the ``git`` executable via PATH.

    Returns:
        Absolute path from :func:`shutil.which` when found, else the string
        ``git`` for a best-effort lookup at exec time.
    """
    found = shutil.which("git")
    return found if found else "git"


async def _git_run_async(
    git_args: list[str],
    *,
    cwd: str | None = None,
    timeout: float | None = 30.0,
) -> tuple[int, str, str]:
    """Run ``git`` with arguments under asyncio, decoding stdout/stderr as UTF-8.

    Args:
        git_args: Arguments after ``git`` (e.g. ``[\"status\", \"--porcelain\"]``).
        cwd: Working directory; defaults to :func:`os.getcwd`.
        timeout: Seconds to wait for completion; ``None`` waits indefinitely.
            On timeout, sends ``124`` and a timeout message (aligned with common
            ``timeout`` exit codes).

    Returns:
        Tuple of ``(returncode, stdout, stderr)``. Return code ``127`` if the
        git binary is missing; ``124`` on timeout.
    """
    exe = git_exe()
    workdir = cwd if cwd is not None else os.getcwd()
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        proc = await asyncio.create_subprocess_exec(
            exe,
            *git_args,
            cwd=workdir,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return 127, "", "git executable not found"

    try:
        if timeout is not None:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        else:
            stdout_b, stderr_b = await proc.communicate()
    except TimeoutError:
        proc.kill()
        await proc.wait()
        return 124, "", "git command timed out"

    rc = proc.returncode if proc.returncode is not None else -1
    return (
        rc,
        stdout_b.decode("utf-8", errors="replace"),
        stderr_b.decode("utf-8", errors="replace"),
    )


class GitStatus(NamedTuple):
    """One file entry from :func:`get_git_status`.

    Attributes:
        path: Repository-relative path.
        status: Index/worktree code (e.g. ``M``, ``A``, ``?``).
        is_staged: True if the line reflected index (staged) state.
    """

    path: str
    status: str  # M, A, D, R, etc.
    is_staged: bool


@lru_cache(maxsize=50)
def find_git_root(start_path: str) -> str | None:
    """Walk parents from ``start_path`` until a ``.git`` file or directory exists.

    Args:
        start_path: Any path inside a potential work tree.

    Returns:
        Absolute path to the directory containing ``.git``, or None if not
        inside a repository.
    """
    current = os.path.abspath(start_path)
    root = os.path.splitdrive(current)[0] or "/"
    if root and not root.endswith(os.sep):
        root += os.sep

    while current != root:
        git_path = os.path.join(current, ".git")
        try:
            if os.path.isdir(git_path) or os.path.isfile(git_path):
                return current
        except Exception:
            pass

        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    # Check root directory
    try:
        git_path = os.path.join(root, ".git")
        if os.path.isdir(git_path) or os.path.isfile(git_path):
            return root
    except Exception:
        pass

    return None


def find_canonical_git_root(start_path: str) -> str | None:
    """
    Find the canonical git repository root, resolving through worktrees.

    Unlike find_git_root, this returns the main repository's working directory.
    """
    git_root = find_git_root(start_path)
    if not git_root:
        return None

    return _resolve_canonical_root(git_root)


@lru_cache(maxsize=50)
def _resolve_canonical_root(git_root: str) -> str:
    """Resolve a git root to the canonical main repository root."""
    try:
        git_file = os.path.join(git_root, ".git")

        # In a worktree, .git is a file containing: gitdir: <path>
        if not os.path.isfile(git_file):
            return git_root

        with open(git_file, encoding="utf-8") as f:
            content = f.read().strip()

        if not content.startswith("gitdir:"):
            return git_root

        worktree_git_dir = os.path.normpath(os.path.join(git_root, content[len("gitdir:") :].strip()))

        # Read commondir
        commondir_file = os.path.join(worktree_git_dir, "commondir")
        try:
            with open(commondir_file, encoding="utf-8") as f:
                common_dir = os.path.normpath(os.path.join(worktree_git_dir, f.read().strip()))
        except FileNotFoundError:
            # Submodules don't have commondir
            return git_root

        # Validate structure
        if os.path.dirname(worktree_git_dir) != os.path.join(common_dir, "worktrees"):
            return git_root

        if os.path.basename(common_dir) != ".git":
            return common_dir

        return os.path.dirname(common_dir)
    except Exception:
        return git_root


def get_current_branch(cwd: str | None = None) -> str | None:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip()
        return branch if branch != "HEAD" else None
    except Exception:
        return None


def get_default_branch(cwd: str | None = None) -> str:
    """Get the default branch name (main or master)."""
    try:
        # Try to get from remote HEAD
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD", "--short"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            if "/" in branch:
                return branch.split("/")[-1]
            return branch
    except Exception:
        pass

    # Fallback: check if main or master exists
    for branch in ["main", "master"]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch],
                cwd=cwd,
                capture_output=True,
                check=True,
            )
            if result.returncode == 0:
                return branch
        except Exception:
            continue

    return "main"


def get_head_sha(cwd: str | None = None) -> str | None:
    """Get the current HEAD commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def get_remote_url(cwd: str | None = None, remote: str = "origin") -> str | None:
    """Get the URL of a remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", remote],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def is_shallow_clone(cwd: str | None = None) -> bool:
    """Check if the repository is a shallow clone."""
    git_root = find_git_root(cwd or os.getcwd())
    if not git_root:
        return False

    return os.path.exists(os.path.join(git_root, ".git", "shallow"))


def get_git_status(cwd: str | None = None) -> list[GitStatus]:
    """Get the git status as a list of file statuses."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "-z"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        statuses = []
        for entry in result.stdout.split("\0"):
            if len(entry) < 3:
                continue

            index_status = entry[0]
            worktree_status = entry[1]
            path = entry[3:]

            if index_status == "?" and worktree_status == "?":
                statuses.append(GitStatus(path, "?", False))
                continue

            if index_status != " " and index_status != "?":
                statuses.append(GitStatus(path, index_status, True))
            if worktree_status != " " and worktree_status != "?":
                statuses.append(GitStatus(path, worktree_status, False))

        return statuses
    except Exception:
        return []


def get_staged_files(cwd: str | None = None) -> list[str]:
    """Get list of staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except Exception:
        return []


def get_modified_files(cwd: str | None = None) -> list[str]:
    """Get list of modified (but not staged) files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except Exception:
        return []


def get_untracked_files(cwd: str | None = None) -> list[str]:
    """Get list of untracked files."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except Exception:
        return []


def git_diff(
    path: str | None = None,
    cwd: str | None = None,
    staged: bool = False,
    context: int = 3,
) -> str | None:
    """
    Get the diff for a file or the entire repository.

    Args:
        path: File path (None for entire repo)
        cwd: Working directory
        staged: Include only staged changes
        context: Number of context lines

    Returns:
        The diff output or None on error
    """
    try:
        cmd = ["git", "diff", f"-U{context}"]
        if staged:
            cmd.append("--cached")
        if path:
            cmd.extend(["--", path])

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except Exception:
        return None


def git_show(
    ref: str,
    path: str | None = None,
    cwd: str | None = None,
) -> str | None:
    """
    Show the content of a file at a specific ref.

    Args:
        ref: Git reference (commit, branch, tag)
        path: File path
        cwd: Working directory

    Returns:
        The file content or None on error
    """
    try:
        spec = f"{ref}:{path}" if path else ref
        result = subprocess.run(
            ["git", "show", spec],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except Exception:
        return None


def git_log(
    path: str | None = None,
    cwd: str | None = None,
    max_count: int = 10,
    format_str: str = "%H %s",
) -> list[str]:
    """
    Get git log entries.

    Args:
        path: File path (None for entire repo)
        cwd: Working directory
        max_count: Maximum number of entries
        format_str: Git log format string

    Returns:
        List of log entries
    """
    try:
        cmd = ["git", "log", f"--max-count={max_count}", f"--format={format_str}"]
        if path:
            cmd.extend(["--", path])

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return [line for line in result.stdout.strip().split("\n") if line]
    except Exception:
        return []


def is_git_ignored(path: str, cwd: str | None = None) -> bool:
    """Check if a file is git ignored."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", path],
            cwd=cwd,
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def git_add(
    paths: list[str],
    cwd: str | None = None,
) -> bool:
    """Add files to git staging area."""
    try:
        subprocess.run(
            ["git", "add", "--"] + paths,
            cwd=cwd,
            check=True,
        )
        return True
    except Exception as e:
        log_error(e)
        return False


def git_commit(
    message: str,
    cwd: str | None = None,
) -> bool:
    """Create a git commit."""
    try:
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=cwd,
            check=True,
        )
        return True
    except Exception as e:
        log_error(e)
        return False


# Async helpers for context / UI (use asyncio.subprocess)


async def get_is_git(cwd: str | None = None) -> bool:
    """Return True if ``cwd`` is inside a git work tree (uses ``git rev-parse``)."""
    rc, out, _ = await _git_run_async(
        ["rev-parse", "--is-inside-work-tree"],
        cwd=cwd,
        timeout=10.0,
    )
    return rc == 0 and out.strip().lower() == "true"


async def get_branch(cwd: str | None = None) -> str:
    """Get the current branch name (async). Detached HEAD yields ``main``."""
    rc, out, _ = await _git_run_async(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        cwd=cwd,
        timeout=10.0,
    )
    if rc != 0:
        return "main"
    branch = out.strip()
    if not branch or branch == "HEAD":
        return "main"
    return branch


async def get_default_branch_async(cwd: str | None = None) -> str:
    """
    Async default branch resolution (same semantics as :func:`get_default_branch`).
    """
    return await asyncio.to_thread(get_default_branch, cwd)


async def exec_git_command(
    args: list[str],
    cwd: str | None = None,
    *,
    timeout: float = 120.0,
) -> str:
    """
    Run ``git`` with the given arguments; return stdout on success, else empty string.

    Uses the resolved :func:`git_exe` and disables terminal prompts for non-interactive use.
    """
    rc, out, _ = await _git_run_async(args, cwd=cwd, timeout=timeout)
    return out if rc == 0 else ""
