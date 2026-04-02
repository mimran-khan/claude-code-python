"""
Setup and initialization for Claude Code.

This module handles application setup, including environment validation,
worktree creation, permission checks, and background job initialization.

Migrated from: setup.ts (477 lines)
"""

from __future__ import annotations

import os
import sys
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


async def setup(
    cwd: str,
    permission_mode: str = "default",
    allow_dangerously_skip_permissions: bool = False,
    worktree_enabled: bool = False,
    worktree_name: str | None = None,
    tmux_enabled: bool = False,
    custom_session_id: str | None = None,
    worktree_pr_number: int | None = None,
    messaging_socket_path: str | None = None,
) -> None:
    """
    Set up the Claude Code environment.

    This function performs:
    1. Python version check (requires 3.10+)
    2. Session initialization
    3. Working directory setup
    4. Hooks configuration capture
    5. Worktree creation (if requested)
    6. Background job initialization
    7. Permission validation

    Args:
        cwd: The working directory to use
        permission_mode: Permission mode ('default', 'plan', 'bypassPermissions')
        allow_dangerously_skip_permissions: Skip permission checks (dangerous!)
        worktree_enabled: Create a worktree for this session
        worktree_name: Name for the worktree
        tmux_enabled: Create a tmux session for the worktree
        custom_session_id: Custom session ID to use
        worktree_pr_number: PR number for worktree naming
        messaging_socket_path: UDS messaging socket path
    """
    from .bootstrap.state import (
        switch_session,
    )
    from .utils.cwd import set_cwd
    from .utils.log import log_for_diagnostics

    log_for_diagnostics("info", "setup_started")

    # Check Python version

    # Set custom session ID if provided
    if custom_session_id:
        switch_session(custom_session_id)

    # Set working directory
    set_cwd(cwd)
    os.chdir(cwd)

    # Gated config/settings migrations (``main.tsx`` ``runMigrations`` parity)
    if not os.getenv("PYTEST_CURRENT_TEST"):
        try:
            from .migrations.startup import run_sync_migrations

            run_sync_migrations()
        except Exception as exc:
            log_for_diagnostics(
                "warning",
                "migrations_sync_failed",
                {"error": str(exc)},
            )

    # Capture hooks configuration snapshot
    hooks_start = time.time()
    try:
        from .hooks.config_snapshot import capture_hooks_config_snapshot

        capture_hooks_config_snapshot()
        log_for_diagnostics(
            "info",
            "setup_hooks_captured",
            {"duration_ms": int((time.time() - hooks_start) * 1000)},
        )
    except ImportError:
        pass

    # Initialize file changed watcher
    try:
        from .hooks.file_changed import initialize_file_changed_watcher

        initialize_file_changed_watcher(cwd)
    except ImportError:
        pass

    # Handle worktree creation if requested
    if worktree_enabled:
        await _setup_worktree(
            cwd,
            worktree_name,
            worktree_pr_number,
            tmux_enabled,
        )

    # Background jobs initialization
    log_for_diagnostics("info", "setup_background_jobs_starting")

    is_bare_mode = _is_bare_mode()

    if not is_bare_mode:
        # Initialize session memory
        try:
            from .services.session_memory import init_session_memory

            init_session_memory()
        except ImportError:
            pass

    # Initialize analytics sinks
    try:
        from .utils.sinks import init_sinks

        init_sinks()
    except ImportError:
        pass

    log_for_diagnostics("info", "setup_background_jobs_launched")

    # Log session start event
    try:
        from .services.analytics import log_event

        log_event("tengu_started", {})
    except ImportError:
        pass

    # Validate permission mode
    if permission_mode == "bypassPermissions" or allow_dangerously_skip_permissions:
        await _validate_bypass_permissions(permission_mode)

    # Skip additional setup in test mode
    if os.getenv("NODE_ENV") == "test" or os.getenv("PYTEST_CURRENT_TEST"):
        return

    # Log previous session exit event
    try:
        from .config import get_current_project_config
        from .services.analytics import log_event

        project_config = get_current_project_config()
        if project_config.get("last_cost") is not None and project_config.get("last_duration") is not None:
            log_event(
                "tengu_exit",
                {
                    "last_session_cost": project_config.get("last_cost"),
                    "last_session_api_duration": project_config.get("last_api_duration"),
                    "last_session_tool_duration": project_config.get("last_tool_duration"),
                    "last_session_duration": project_config.get("last_duration"),
                    "last_session_lines_added": project_config.get("last_lines_added"),
                    "last_session_lines_removed": project_config.get("last_lines_removed"),
                    "last_session_id": project_config.get("last_session_id"),
                },
            )
    except ImportError:
        pass


def _is_bare_mode() -> bool:
    """Check if running in bare/simple mode."""
    from .utils.env import is_env_truthy

    return is_env_truthy(os.getenv("CLAUDE_CODE_SIMPLE"))


async def _setup_worktree(
    cwd: str,
    worktree_name: str | None,
    worktree_pr_number: int | None,
    tmux_enabled: bool,
) -> None:
    """Set up worktree for the session."""
    from .bootstrap.state import get_session_id, set_original_cwd, set_project_root
    from .utils.cwd import get_cwd, set_cwd
    from .utils.git import get_is_git

    # Check if in a git repository
    is_git = await get_is_git()
    if not is_git:
        print(
            f"\033[31mError: Can only use --worktree in a git repository, but {cwd} is not a git repository.\033[0m",
            file=sys.stderr,
        )
        sys.exit(1)

    # Generate worktree slug
    slug = f"pr-{worktree_pr_number}" if worktree_pr_number else (worktree_name or "worktree")

    try:
        from .utils.worktree import create_worktree_for_session

        worktree_session = await create_worktree_for_session(
            get_session_id(),
            slug,
            pr_number=worktree_pr_number,
        )

        os.chdir(worktree_session.worktree_path)
        set_cwd(worktree_session.worktree_path)
        set_original_cwd(get_cwd())
        set_project_root(get_cwd())

        if tmux_enabled:
            try:
                from .utils.worktree import create_tmux_session_for_worktree

                await create_tmux_session_for_worktree(
                    worktree_session.session_name,
                    worktree_session.worktree_path,
                )
                print(
                    f"\033[32mCreated tmux session: {worktree_session.session_name}\n"
                    f"To attach: tmux attach -t {worktree_session.session_name}\033[0m"
                )
            except Exception as e:
                print(
                    f"\033[33mWarning: Failed to create tmux session: {e}\033[0m",
                    file=sys.stderr,
                )

    except Exception as e:
        print(f"\033[31mError creating worktree: {e}\033[0m", file=sys.stderr)
        sys.exit(1)


async def _validate_bypass_permissions(permission_mode: str) -> None:
    """
    Validate that bypass permissions mode is safe to use.

    Bypass mode is only allowed in sandboxed environments without internet access.
    """
    import platform

    # Check if running as root on Unix-like systems
    if platform.system() != "Windows" and os.geteuid() == 0:
        is_sandbox = os.getenv("IS_SANDBOX") == "1"
        is_bubblewrap = os.getenv("CLAUDE_CODE_BUBBLEWRAP", "").lower() in ("1", "true")

        if not is_sandbox and not is_bubblewrap:
            print(
                "--dangerously-skip-permissions cannot be used with root/sudo privileges for security reasons",
                file=sys.stderr,
            )
            sys.exit(1)

    # For internal users, enforce sandbox requirement
    if os.getenv("USER_TYPE") == "ant":
        entrypoint = os.getenv("CLAUDE_CODE_ENTRYPOINT", "")
        if entrypoint not in ("local-agent", "claude-desktop"):
            is_docker = await _is_docker()
            is_bubblewrap = os.getenv("CLAUDE_CODE_BUBBLEWRAP", "").lower() in (
                "1",
                "true",
            )
            is_sandbox = os.getenv("IS_SANDBOX") == "1"
            has_internet = await _has_internet_access()

            is_sandboxed = is_docker or is_bubblewrap or is_sandbox
            if not is_sandboxed or has_internet:
                print(
                    f"--dangerously-skip-permissions can only be used in Docker/sandbox "
                    f"containers with no internet access but got Docker: {is_docker}, "
                    f"Bubblewrap: {is_bubblewrap}, IS_SANDBOX: {is_sandbox}, "
                    f"hasInternet: {has_internet}",
                    file=sys.stderr,
                )
                sys.exit(1)


async def _is_docker() -> bool:
    """Check if running inside Docker."""
    # Check for /.dockerenv file
    if os.path.exists("/.dockerenv"):
        return True

    # Check cgroup for docker
    try:
        with open("/proc/1/cgroup") as f:
            content = f.read()
            return "docker" in content or "containerd" in content
    except (FileNotFoundError, PermissionError):
        pass

    return False


async def _has_internet_access() -> bool:
    """Check if internet access is available."""
    import socket

    try:
        with socket.create_connection(("8.8.8.8", 53), timeout=3):
            return True
    except OSError:
        return False
