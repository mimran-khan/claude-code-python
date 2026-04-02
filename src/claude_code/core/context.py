"""Context management for system and user context."""

import asyncio
import os
import subprocess
from functools import cache

from ..constants.common import get_local_iso_date
from ..utils.cwd import get_cwd
from ..utils.git import get_branch, get_default_branch_async, get_is_git, git_exe


class ExecResult:
    """Result from executing a command."""

    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


async def exec_file_no_throw(
    cmd: str,
    args: list[str],
    cwd: str | None = None,
) -> ExecResult:
    """Execute a command without throwing, returning result."""
    try:
        result = subprocess.run(
            [cmd] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return ExecResult(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )
    except Exception as e:
        return ExecResult(stderr=str(e), returncode=1)


MAX_STATUS_CHARS = 2000

# System prompt injection for cache breaking (ephemeral debugging state)
_system_prompt_injection: str | None = None


def get_system_prompt_injection() -> str | None:
    """Get the current system prompt injection."""
    return _system_prompt_injection


def set_system_prompt_injection(value: str | None) -> None:
    """Set the system prompt injection and clear context caches."""
    global _system_prompt_injection
    _system_prompt_injection = value
    # Clear caches when injection changes
    get_user_context.cache_clear()
    get_system_context.cache_clear()


async def get_git_status() -> str | None:
    """Get git status information for the system prompt.

    Returns a formatted string with branch, status, and recent commits.
    """
    if os.environ.get("NODE_ENV") == "test":
        return None

    is_git = await get_is_git()
    if not is_git:
        return None

    try:
        # Run git commands in parallel
        branch_task = asyncio.create_task(get_branch())
        main_branch_task = asyncio.create_task(get_default_branch_async())

        status_result = await exec_file_no_throw(
            git_exe(),
            ["--no-optional-locks", "status", "--short"],
        )
        status = status_result.stdout.strip() if status_result.stdout else ""

        log_result = await exec_file_no_throw(
            git_exe(),
            ["--no-optional-locks", "log", "--oneline", "-n", "5"],
        )
        log = log_result.stdout.strip() if log_result.stdout else ""

        user_name_result = await exec_file_no_throw(
            git_exe(),
            ["config", "user.name"],
        )
        user_name = user_name_result.stdout.strip() if user_name_result.stdout else ""

        branch = await branch_task
        main_branch = await main_branch_task

        # Truncate status if too long
        if len(status) > MAX_STATUS_CHARS:
            status = (
                status[:MAX_STATUS_CHARS] + "\n... (truncated because it exceeds 2k characters. "
                'If you need more information, run "git status" using BashTool)'
            )

        lines = [
            "This is the git status at the start of the conversation. "
            "Note that this status is a snapshot in time, and will not update during the conversation.",
            f"Current branch: {branch}",
            f"Main branch (you will usually use this for PRs): {main_branch}",
        ]
        if user_name:
            lines.append(f"Git user: {user_name}")
        if status:
            lines.append(f"Status:\n{status}")
        if log:
            lines.append(f"Recent commits:\n{log}")

        return "\n".join(lines)

    except Exception:
        return None


@cache
def get_user_context() -> dict[str, str]:
    """Get user context information (memoized).

    Returns a dictionary with user-specific context like date, etc.
    """
    return {
        "date": get_local_iso_date(),
        "cwd": get_cwd(),
    }


@cache
def get_system_context() -> dict[str, str]:
    """Get system context information (memoized).

    Returns a dictionary with system-level context.
    """
    import platform

    return {
        "platform": platform.system().lower(),
        "shell": os.environ.get("SHELL", "unknown"),
        "os_version": f"{platform.system()} {platform.release()}",
    }


async def get_additional_directories_for_claude_md() -> list[str]:
    """Get additional directories for CLAUDE.md loading."""
    # Placeholder - would implement directory discovery
    return []


def set_cached_claude_md_content(content: str) -> None:
    """Set cached CLAUDE.md content."""
    # Placeholder - would implement caching
    pass
