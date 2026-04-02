"""
Memory directory paths.

Path utilities for memory system.

Migrated from: memdir/paths.ts + teamMemPaths.ts
"""

from __future__ import annotations

import os

from ..utils.config_utils import get_claude_config_dir
from ..utils.env_utils import is_env_truthy


def get_memory_dir(project_dir: str | None = None) -> str:
    """
    Get the memory directory path.

    Args:
        project_dir: Project directory (uses cwd if None)

    Returns:
        Path to memory directory
    """
    if project_dir is None:
        project_dir = os.getcwd()

    return os.path.join(project_dir, ".claude", "memory")


def get_auto_mem_path(project_dir: str | None = None) -> str:
    """
    Get the auto memory file path.

    Args:
        project_dir: Project directory

    Returns:
        Path to auto memory file
    """
    return os.path.join(get_memory_dir(project_dir), "auto.md")


def get_memory_entrypoint(project_dir: str | None = None) -> str:
    """
    Get the MEMORY.md entrypoint path.

    Args:
        project_dir: Project directory

    Returns:
        Path to MEMORY.md
    """
    from .memory import ENTRYPOINT_NAME

    return os.path.join(get_memory_dir(project_dir), ENTRYPOINT_NAME)


def is_auto_memory_enabled() -> bool:
    """
    Check if auto memory is enabled.

    Returns:
        True if enabled
    """
    # Check environment variable
    return not is_env_truthy(os.getenv("CLAUDE_CODE_DISABLE_AUTO_MEMORY"))


def get_team_mem_path() -> str:
    """
    Get the team memory path.

    Returns:
        Path to team memory directory
    """
    return os.path.join(get_claude_config_dir(), "team_memory")


def is_team_mem_path(file_path: str) -> bool:
    """True if ``file_path`` is under the team memory directory."""
    team = os.path.realpath(get_team_mem_path())
    try:
        resolved = os.path.realpath(file_path)
    except OSError:
        return False
    if resolved == team:
        return True
    prefix = team + os.sep
    return resolved.startswith(prefix)


def ensure_memory_dir(project_dir: str | None = None) -> str:
    """
    Ensure memory directory exists.

    Args:
        project_dir: Project directory

    Returns:
        Path to memory directory
    """
    memory_dir = get_memory_dir(project_dir)
    os.makedirs(memory_dir, exist_ok=True)
    return memory_dir
