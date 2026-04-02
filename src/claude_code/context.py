"""
Context management for system and user context.

This module handles building the system and user context that gets
prepended to conversations, including git status and CLAUDE.md content.

Migrated from: context.ts (190 lines)
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from functools import lru_cache

from .utils.env import is_env_truthy
from .utils.log import log_error, log_for_diagnostics

MAX_STATUS_CHARS = 2000

# System prompt injection for cache breaking
_system_prompt_injection: str | None = None


def get_system_prompt_injection() -> str | None:
    """Get the current system prompt injection."""
    return _system_prompt_injection


def set_system_prompt_injection(value: str | None) -> None:
    """Set the system prompt injection and clear context caches."""
    global _system_prompt_injection
    _system_prompt_injection = value
    # Clear caches
    get_user_context.cache_clear()
    get_system_context.cache_clear()


@lru_cache(maxsize=1)
async def get_git_status() -> str | None:
    """
    Get the current git status for the system context.

    Returns a formatted string with branch, status, and recent commits.
    """
    if os.getenv("NODE_ENV") == "test" or os.getenv("PYTEST_CURRENT_TEST"):
        return None

    start_time = time.time()
    log_for_diagnostics("info", "git_status_started")

    try:
        from .utils.git import (
            exec_git_command,
            get_branch,
            get_default_branch_async,
            get_is_git,
        )

        is_git_start = time.time()
        is_git = await get_is_git()
        log_for_diagnostics(
            "info",
            "git_is_git_check_completed",
            {
                "duration_ms": int((time.time() - is_git_start) * 1000),
                "is_git": is_git,
            },
        )

        if not is_git:
            log_for_diagnostics(
                "info",
                "git_status_skipped_not_git",
                {"duration_ms": int((time.time() - start_time) * 1000)},
            )
            return None

        git_cmds_start = time.time()

        # Run git commands
        branch = await get_branch()
        main_branch = await get_default_branch_async()
        status_result = await exec_git_command(["--no-optional-locks", "status", "--short"])
        log_result = await exec_git_command(["--no-optional-locks", "log", "--oneline", "-n", "5"])
        user_result = await exec_git_command(["config", "user.name"])

        status = status_result.strip() if status_result else ""
        log = log_result.strip() if log_result else ""
        user_name = user_result.strip() if user_result else ""

        log_for_diagnostics(
            "info",
            "git_commands_completed",
            {
                "duration_ms": int((time.time() - git_cmds_start) * 1000),
                "status_length": len(status),
            },
        )

        # Truncate long status
        if len(status) > MAX_STATUS_CHARS:
            truncated_status = (
                status[:MAX_STATUS_CHARS] + "\n... (truncated because it exceeds 2k characters. "
                'If you need more information, run "git status" using BashTool)'
            )
        else:
            truncated_status = status

        log_for_diagnostics(
            "info",
            "git_status_completed",
            {
                "duration_ms": int((time.time() - start_time) * 1000),
                "truncated": len(status) > MAX_STATUS_CHARS,
            },
        )

        lines = [
            "This is the git status at the start of the conversation. "
            "Note that this status is a snapshot in time, and will not update "
            "during the conversation.",
            f"Current branch: {branch}",
            f"Main branch (you will usually use this for PRs): {main_branch}",
        ]

        if user_name:
            lines.append(f"Git user: {user_name}")

        lines.extend(
            [
                f"Status:\n{truncated_status or '(clean)'}",
                f"Recent commits:\n{log}",
            ]
        )

        return "\n\n".join(lines)

    except Exception as e:
        log_for_diagnostics(
            "error",
            "git_status_failed",
            {"duration_ms": int((time.time() - start_time) * 1000)},
        )
        log_error(e)
        return None


@lru_cache(maxsize=1)
async def get_system_context() -> dict[str, str]:
    """
    Get the system context to prepend to conversations.

    This is cached for the duration of the conversation.
    """
    start_time = time.time()
    log_for_diagnostics("info", "system_context_started")

    # Skip git status in CCR or when disabled
    should_skip_git = is_env_truthy(os.getenv("CLAUDE_CODE_REMOTE"))

    if not should_skip_git:
        try:
            from .utils.git_settings import should_include_git_instructions

            if not should_include_git_instructions():
                should_skip_git = True
        except ImportError:
            pass

    git_status = None if should_skip_git else await get_git_status()

    # Include system prompt injection if set
    injection = get_system_prompt_injection()

    log_for_diagnostics(
        "info",
        "system_context_completed",
        {
            "duration_ms": int((time.time() - start_time) * 1000),
            "has_git_status": git_status is not None,
            "has_injection": injection is not None,
        },
    )

    result: dict[str, str] = {}
    if git_status:
        result["gitStatus"] = git_status
    if injection:
        result["cacheBreaker"] = f"[CACHE_BREAKER: {injection}]"

    return result


def _get_local_iso_date() -> str:
    """Get the current local date in ISO format."""
    return datetime.now(UTC).strftime("%Y-%m-%d")


@lru_cache(maxsize=1)
async def get_user_context() -> dict[str, str]:
    """
    Get the user context to prepend to conversations.

    This is cached for the duration of the conversation.
    """
    start_time = time.time()
    log_for_diagnostics("info", "user_context_started")

    # Check if CLAUDE.md is disabled
    should_disable_claude_md = is_env_truthy(os.getenv("CLAUDE_CODE_DISABLE_CLAUDE_MDS"))

    if not should_disable_claude_md:
        # Also check bare mode
        from .utils.env import is_bare_mode

        if is_bare_mode():
            try:
                from .bootstrap.state import get_additional_directories_for_claude_md

                if not get_additional_directories_for_claude_md():
                    should_disable_claude_md = True
            except ImportError:
                should_disable_claude_md = True

    claude_md = None
    if not should_disable_claude_md:
        try:
            from .utils.claudemd import (
                filter_injected_memory_files,
                get_claude_mds,
                get_memory_files,
            )

            memory_files = await get_memory_files()
            filtered_files = filter_injected_memory_files(memory_files)
            claude_md = get_claude_mds(filtered_files)
        except ImportError:
            pass

    # Cache for auto-mode classifier
    try:
        from .bootstrap.state import set_cached_claude_md_content

        set_cached_claude_md_content(claude_md)
    except ImportError:
        pass

    log_for_diagnostics(
        "info",
        "user_context_completed",
        {
            "duration_ms": int((time.time() - start_time) * 1000),
            "claudemd_length": len(claude_md) if claude_md else 0,
            "claudemd_disabled": should_disable_claude_md,
        },
    )

    result: dict[str, str] = {}
    if claude_md:
        result["claudeMd"] = claude_md
    result["currentDate"] = f"Today's date is {_get_local_iso_date()}."

    return result


def clear_context_caches() -> None:
    """Clear all context caches."""
    get_git_status.cache_clear()
    get_system_context.cache_clear()
    get_user_context.cache_clear()
