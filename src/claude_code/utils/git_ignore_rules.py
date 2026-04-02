"""
Global gitignore helpers and `git check-ignore` wrapper.

Migrated from: utils/git/gitignore.ts
"""

from __future__ import annotations

import asyncio
import os
import subprocess

from .cwd import get_cwd
from .git import find_git_root
from .log import log_error


async def is_path_gitignored(file_path: str, cwd: str) -> bool:
    """Return True if git reports the path as ignored (exit 0)."""

    def _check() -> bool:
        try:
            r = subprocess.run(
                ["git", "check-ignore", file_path],
                cwd=cwd,
                capture_output=True,
                check=False,
            )
            return r.returncode == 0
        except OSError:
            return False

    return await asyncio.to_thread(_check)


def get_global_gitignore_path() -> str:
    return os.path.join(os.path.expanduser("~"), ".config", "git", "ignore")


async def add_file_glob_rule_to_gitignore(filename: str, cwd: str | None = None) -> None:
    base = cwd or get_cwd()
    if find_git_root(base) is None:
        return

    gitignore_entry = f"**/{filename}"
    test_path = f"{filename}sample-file.txt" if filename.endswith("/") else filename
    if await is_path_gitignored(test_path, base):
        return

    global_path = get_global_gitignore_path()
    config_git_dir = os.path.dirname(global_path)
    os.makedirs(config_git_dir, exist_ok=True)

    try:
        if os.path.isfile(global_path):
            with open(global_path, encoding="utf-8") as f:
                content = f.read()
            if gitignore_entry in content:
                return
            with open(global_path, "a", encoding="utf-8") as f:
                f.write(f"\n{gitignore_entry}\n")
        else:
            with open(global_path, "w", encoding="utf-8") as f:
                f.write(f"{gitignore_entry}\n")
    except Exception as e:
        log_error(e)
