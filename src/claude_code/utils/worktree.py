"""
Git worktree helpers (validation, paths, PR parsing, basic create/remove).

Migrated from: utils/worktree.ts (core subset).
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cwd import get_cwd
from .debug import log_for_debugging
from .git import find_git_root, get_current_branch, get_default_branch, git_exe

_VALID_SLUG_SEGMENT = re.compile(r"^[a-zA-Z0-9._-]+$")
_MAX_SLUG_LEN = 64


def validate_worktree_slug(slug: str) -> None:
    if len(slug) > _MAX_SLUG_LEN:
        raise ValueError(f"Invalid worktree name: must be {_MAX_SLUG_LEN} characters or fewer (got {len(slug)})")
    for segment in slug.split("/"):
        if segment in (".", ".."):
            raise ValueError(f'Invalid worktree name "{slug}": must not contain "." or ".." path segments')
        if not _VALID_SLUG_SEGMENT.fullmatch(segment):
            raise ValueError(
                f'Invalid worktree name "{slug}": each segment must be non-empty and alphanumeric / ._- only'
            )


def flatten_slug(slug: str) -> str:
    return slug.replace("/", "+")


def worktree_branch_name(slug: str) -> str:
    return f"worktree-{flatten_slug(slug)}"


def _worktrees_dir(repo_root: str) -> Path:
    return Path(repo_root) / ".claude" / "worktrees"


def worktree_path_for(repo_root: str, slug: str) -> str:
    return str(_worktrees_dir(repo_root) / flatten_slug(slug))


def parse_pr_reference(text: str) -> int | None:
    m = re.match(
        r"^https?://[^/]+/[^/]+/[^/]+/pull/(\d+)/?(?:[?#].*)?$",
        text,
        re.I,
    )
    if m:
        return int(m.group(1), 10)
    hm = re.match(r"^#(\d+)$", text)
    if hm:
        return int(hm.group(1), 10)
    return None


def generate_tmux_session_name(repo_path: str, branch: str) -> str:
    base = Path(repo_path).name
    return re.sub(r"[/.]", "_", f"{base}_{branch}")


@dataclass
class WorktreeSession:
    original_cwd: str
    worktree_path: str
    worktree_name: str
    worktree_branch: str | None = None
    original_branch: str | None = None
    original_head_commit: str | None = None
    session_id: str = ""
    tmux_session_name: str | None = None
    hook_based: bool = False


_current: WorktreeSession | None = None


def get_current_worktree_session() -> WorktreeSession | None:
    return _current


def restore_worktree_session(session: WorktreeSession | None) -> None:
    global _current
    _current = session


def has_worktree_create_hook() -> bool:
    return False


async def _run_git(args: list[str], cwd: str, extra_env: dict[str, str] | None = None) -> tuple[int, str, str]:
    g = git_exe()
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": ""}
    if extra_env:
        env.update(extra_env)
    p = await asyncio.create_subprocess_exec(
        g,
        *args,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await p.communicate()
    return p.returncode or 0, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


async def get_or_create_worktree(
    repo_root: str,
    slug: str,
    pr_number: int | None = None,
) -> dict[str, Any]:
    validate_worktree_slug(slug)
    wt_path = worktree_path_for(repo_root, slug)
    branch = worktree_branch_name(slug)
    _worktrees_dir(repo_root).mkdir(parents=True, exist_ok=True)

    if Path(wt_path).is_dir() and (Path(wt_path) / ".git").exists():
        code, sha_out, _ = await _run_git(["rev-parse", "HEAD"], cwd=wt_path)
        if code == 0 and sha_out.strip():
            return {
                "worktree_path": wt_path,
                "worktree_branch": branch,
                "head_commit": sha_out.strip(),
                "existed": True,
            }

    if pr_number is not None:
        code, _, e = await _run_git(
            ["fetch", "origin", f"pull/{pr_number}/head"],
            cwd=repo_root,
        )
        if code != 0:
            raise RuntimeError(f"Failed to fetch PR #{pr_number}: {e.strip()}")
        base_branch = "FETCH_HEAD"
    else:
        default = get_default_branch(repo_root)
        code, _, _ = await _run_git(
            ["fetch", "origin", default],
            cwd=repo_root,
        )
        base_branch = f"origin/{default}" if code == 0 else "HEAD"

    code, _, e = await _run_git(
        ["worktree", "add", "-B", branch, wt_path, base_branch],
        cwd=repo_root,
    )
    if code != 0:
        raise RuntimeError(f"Failed to create worktree: {e.strip()}")

    code, sha_out, e2 = await _run_git(["rev-parse", "HEAD"], cwd=wt_path)
    if code != 0:
        raise RuntimeError(f"Failed to read HEAD: {e2.strip()}")
    return {
        "worktree_path": wt_path,
        "worktree_branch": branch,
        "head_commit": sha_out.strip(),
        "base_branch": base_branch,
        "existed": False,
    }


async def create_worktree_for_session(
    session_id: str,
    slug: str,
    tmux_session_name: str | None = None,
    pr_number: int | None = None,
) -> WorktreeSession:
    global _current
    root = find_git_root(get_cwd())
    if not root:
        raise RuntimeError("Not in a git repository")
    orig_branch = get_current_branch(root)
    res = await get_or_create_worktree(root, slug, pr_number=pr_number)
    _current = WorktreeSession(
        original_cwd=get_cwd(),
        worktree_path=res["worktree_path"],
        worktree_name=slug,
        worktree_branch=res.get("worktree_branch"),
        original_branch=orig_branch,
        original_head_commit=res.get("head_commit"),
        session_id=session_id,
        tmux_session_name=tmux_session_name,
    )

    try:
        from .config_utils import save_current_project_config

        def _upd(c: dict[str, Any]) -> dict[str, Any]:
            c = dict(c)
            c["activeWorktreeSession"] = {
                "originalCwd": _current.original_cwd,
                "worktreePath": _current.worktree_path,
                "worktreeName": _current.worktree_name,
                "worktreeBranch": _current.worktree_branch,
                "sessionId": _current.session_id,
            }
            return c

        save_current_project_config(_upd)
    except Exception as exc:
        log_for_debugging(f"worktree: persist failed: {exc}")
    return _current


async def cleanup_worktree() -> None:
    global _current
    if not _current:
        return
    sess = _current
    os.chdir(sess.original_cwd)
    root = find_git_root(sess.original_cwd)
    if root:
        await _run_git(
            ["worktree", "remove", "--force", sess.worktree_path],
            cwd=root,
        )
        if sess.worktree_branch:
            await asyncio.sleep(0.1)
            await _run_git(["branch", "-D", sess.worktree_branch], cwd=root)
    _current = None
    try:
        from .config_utils import save_current_project_config

        def _clr(c: dict[str, Any]) -> dict[str, Any]:
            c = dict(c)
            c.pop("activeWorktreeSession", None)
            return c

        save_current_project_config(_clr)
    except Exception:
        pass


async def is_tmux_available() -> bool:
    exe = shutil.which("tmux")
    if not exe:
        return False
    p = await asyncio.create_subprocess_exec(
        exe, "-V", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    return (await p.wait()) == 0
