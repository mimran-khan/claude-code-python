"""
Filesystem-based git state reading (no git subprocess for refs).

Migrated from: utils/git/gitFilesystem.ts

Lives alongside utils/git.py to avoid shadowing the git module with a package.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from .cwd import get_cwd
from .git import find_git_root
from .git_config_parser import parse_git_config_value

T = TypeVar("T")

_resolve_git_dir_cache: dict[str, str | None] = {}


def clear_resolve_git_dir_cache() -> None:
    _resolve_git_dir_cache.clear()


async def resolve_git_dir(start_path: str | None = None) -> str | None:
    cwd = os.path.abspath(start_path or get_cwd())
    cached = _resolve_git_dir_cache.get(cwd)
    if cached is not None or cwd in _resolve_git_dir_cache:
        return cached

    root = find_git_root(cwd)
    if not root:
        _resolve_git_dir_cache[cwd] = None
        return None

    git_path = os.path.join(root, ".git")
    try:
        if os.path.isfile(git_path):
            with open(git_path, encoding="utf-8") as f:
                content = f.read().strip()
            if content.startswith("gitdir:"):
                raw = content[len("gitdir:") :].strip()
                resolved = os.path.realpath(os.path.join(root, raw))
                _resolve_git_dir_cache[cwd] = resolved
                return resolved
        _resolve_git_dir_cache[cwd] = git_path
        return git_path
    except OSError:
        _resolve_git_dir_cache[cwd] = None
        return None


def is_safe_ref_name(name: str) -> bool:
    if not name or name.startswith(("-", "/")):
        return False
    if ".." in name:
        return False
    if any(p in (".", "") for p in name.split("/")):
        return False
    return all(ch.isalnum() or ch in "/._+@-" for ch in name)


def is_valid_git_sha(s: str) -> bool:
    return bool(
        (len(s) == 40 and all(c in "0123456789abcdef" for c in s.lower()))
        or (len(s) == 64 and all(c in "0123456789abcdef" for c in s.lower()))
    )


async def read_git_head(git_dir: str) -> dict[str, str] | None:
    try:
        with open(os.path.join(git_dir, "HEAD"), encoding="utf-8") as f:
            content = f.read().strip()
        if content.startswith("ref:"):
            ref = content[len("ref:") :].strip()
            if ref.startswith("refs/heads/"):
                name = ref[len("refs/heads/") :]
                if not is_safe_ref_name(name):
                    return None
                return {"type": "branch", "name": name}
            if not is_safe_ref_name(ref):
                return None
            sha = await resolve_ref(git_dir, ref)
            return {"type": "detached", "sha": sha or ""}
        if not is_valid_git_sha(content):
            return None
        return {"type": "detached", "sha": content}
    except OSError:
        return None


async def resolve_ref(git_dir: str, ref: str) -> str | None:
    result = await _resolve_ref_in_dir(git_dir, ref)
    if result:
        return result
    common = await get_common_dir(git_dir)
    if common and common != git_dir:
        return await _resolve_ref_in_dir(common, ref)
    return None


async def _resolve_ref_in_dir(dir_path: str, ref: str) -> str | None:
    loose = os.path.join(dir_path, *ref.split("/"))
    try:
        with open(loose, encoding="utf-8") as f:
            body = f.read().strip()
        if body.startswith("ref:"):
            target = body[len("ref:") :].strip()
            if not is_safe_ref_name(target):
                return None
            return await resolve_ref(dir_path, target)
        if is_valid_git_sha(body):
            return body
    except OSError:
        pass
    packed = os.path.join(dir_path, "packed-refs")
    try:
        with open(packed, encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or line.startswith("^"):
                    continue
                sp = line.strip().split(" ", 1)
                if len(sp) != 2:
                    continue
                sha, rname = sp
                if rname == ref and is_valid_git_sha(sha):
                    return sha
    except OSError:
        pass
    return None


async def get_common_dir(git_dir: str) -> str | None:
    try:
        with open(os.path.join(git_dir, "commondir"), encoding="utf-8") as f:
            content = f.read().strip()
        return os.path.realpath(os.path.join(git_dir, content))
    except OSError:
        return None


async def read_raw_symref(git_dir: str, ref_path: str, branch_prefix: str) -> str | None:
    try:
        with open(os.path.join(git_dir, *ref_path.split("/")), encoding="utf-8") as f:
            body = f.read().strip()
        if body.startswith("ref:"):
            target = body[len("ref:") :].strip()
            if target.startswith(branch_prefix):
                name = target[len(branch_prefix) :]
                if is_safe_ref_name(name):
                    return name
    except OSError:
        pass
    return None


class _MtimeCache:
    def __init__(self) -> None:
        self._paths: dict[str, str] = {}
        self._mtimes: dict[str, float] = {}
        self._values: dict[str, Any] = {}

    def _stale(self, key: str) -> bool:
        path = self._paths.get(key)
        if not path or not os.path.isfile(path):
            return True
        try:
            m = os.path.getmtime(path)
        except OSError:
            return True
        old = self._mtimes.get(key)
        if old is None or m != old:
            self._mtimes[key] = m
            return True
        return False

    async def get(self, key: str, path: str, compute: Callable[[], Awaitable[T]]) -> T:
        self._paths[key] = path
        if key not in self._values or self._stale(key):
            self._values[key] = await compute()
        return self._values[key]  # type: ignore[no-any-return]


_cache = _MtimeCache()


async def _compute_branch() -> str:
    gd = await resolve_git_dir()
    if not gd:
        return "HEAD"
    head = await read_git_head(gd)
    if not head:
        return "HEAD"
    if head.get("type") == "branch":
        return str(head["name"])
    return "HEAD"


async def _compute_head() -> str:
    gd = await resolve_git_dir()
    if not gd:
        return ""
    head = await read_git_head(gd)
    if not head:
        return ""
    if head.get("type") == "branch":
        name = str(head["name"])
        return (await resolve_ref(gd, f"refs/heads/{name}")) or ""
    return str(head.get("sha", ""))


async def _compute_remote_url() -> str | None:
    gd = await resolve_git_dir()
    if not gd:
        return None
    url = await parse_git_config_value(gd, "remote", "origin", "url")
    if url:
        return url
    common = await get_common_dir(gd)
    if common and common != gd:
        return await parse_git_config_value(common, "remote", "origin", "url")
    return None


async def _compute_default_branch() -> str:
    gd = await resolve_git_dir()
    if not gd:
        return "main"
    common = (await get_common_dir(gd)) or gd
    sym = await read_raw_symref(common, "refs/remotes/origin/HEAD", "refs/remotes/origin/")
    if sym:
        return sym
    for candidate in ("main", "master"):
        if await resolve_ref(common, f"refs/remotes/origin/{candidate}"):
            return candidate
    return "main"


def _head_path(git_dir: str) -> str:
    return os.path.join(git_dir, "HEAD")


async def get_cached_branch() -> str:
    gd = await resolve_git_dir()
    if not gd:
        return await _compute_branch()
    return await _cache.get("branch", _head_path(gd), _compute_branch)


async def get_cached_head() -> str:
    gd = await resolve_git_dir()
    if not gd:
        return await _compute_head()
    return await _cache.get("head", _head_path(gd), _compute_head)


async def get_cached_remote_url() -> str | None:
    gd = await resolve_git_dir()
    if not gd:
        return await _compute_remote_url()
    common = (await get_common_dir(gd)) or gd
    cfg = os.path.join(common, "config")
    return await _cache.get("remoteUrl", cfg, _compute_remote_url)


async def get_cached_default_branch() -> str:
    gd = await resolve_git_dir()
    if not gd:
        return await _compute_default_branch()
    common = (await get_common_dir(gd)) or gd
    p = os.path.join(common, "refs", "remotes", "origin", "HEAD")
    cache_path = p if os.path.isfile(p) else _head_path(gd)
    return await _cache.get("defaultBranch", cache_path, _compute_default_branch)


def reset_git_file_watcher() -> None:
    _cache._paths.clear()
    _cache._mtimes.clear()
    _cache._values.clear()


async def get_head_for_dir(cwd: str) -> str | None:
    gd = await resolve_git_dir(cwd)
    if not gd:
        return None
    head = await read_git_head(gd)
    if not head:
        return None
    if head.get("type") == "branch":
        return await resolve_ref(gd, f"refs/heads/{head['name']}")
    return str(head.get("sha"))


async def read_worktree_head_sha(worktree_path: str) -> str | None:
    try:
        with open(os.path.join(worktree_path, ".git"), encoding="utf-8") as f:
            ptr = f.read().strip()
        if not ptr.startswith("gitdir:"):
            return None
        git_dir = os.path.realpath(os.path.join(worktree_path, ptr[len("gitdir:") :].strip()))
    except OSError:
        return None
    head = await read_git_head(git_dir)
    if not head:
        return None
    if head.get("type") == "branch":
        return await resolve_ref(git_dir, f"refs/heads/{head['name']}")
    return str(head.get("sha"))


async def get_remote_url_for_dir(cwd: str) -> str | None:
    gd = await resolve_git_dir(cwd)
    if not gd:
        return None
    url = await parse_git_config_value(gd, "remote", "origin", "url")
    if url:
        return url
    common = await get_common_dir(gd)
    if common and common != gd:
        return await parse_git_config_value(common, "remote", "origin", "url")
    return None


async def is_shallow_clone() -> bool:
    gd = await resolve_git_dir()
    if not gd:
        return False
    common = (await get_common_dir(gd)) or gd
    return os.path.isfile(os.path.join(common, "shallow"))


async def get_worktree_count_from_fs() -> int:
    try:
        gd = await resolve_git_dir()
        if not gd:
            return 0
        common = (await get_common_dir(gd)) or gd
        wt = os.path.join(common, "worktrees")
        entries = os.listdir(wt)
        return len(entries) + 1
    except OSError:
        return 1
