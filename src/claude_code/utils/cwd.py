"""
Working Directory Utilities.

Provides functions for managing the current working directory.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from contextvars import ContextVar
from typing import TypeVar

T = TypeVar("T")


# Context variable for CWD override
_cwd_override: ContextVar[str | None] = ContextVar("cwd_override", default=None)

# Original CWD at startup
_original_cwd: str = os.getcwd()

# Global CWD state
_global_cwd: str | None = None


def set_global_cwd(cwd: str) -> None:
    """Set the global working directory.

    Args:
        cwd: The working directory
    """
    global _global_cwd
    _global_cwd = cwd


def get_global_cwd() -> str:
    """Get the global working directory.

    Returns:
        The global working directory or current directory
    """
    return _global_cwd or os.getcwd()


def get_original_cwd() -> str:
    """Get the original working directory at startup.

    Returns:
        The original working directory
    """
    return _original_cwd


def run_with_cwd_override(cwd: str, fn: Callable[[], T]) -> T:
    """Run a function with an overridden working directory.

    All calls to pwd()/get_cwd() within the function will return
    the overridden cwd instead of the global one.

    Args:
        cwd: The working directory to use
        fn: The function to run

    Returns:
        The function result
    """
    token = _cwd_override.set(cwd)
    try:
        return fn()
    finally:
        _cwd_override.reset(token)


def pwd() -> str:
    """Get the current working directory.

    Returns the context-specific override if set, otherwise
    the global CWD.

    Returns:
        The current working directory
    """
    override = _cwd_override.get()
    if override is not None:
        return override
    return get_global_cwd()


def get_cwd() -> str:
    """Get the current working directory.

    Returns the context-specific override if set, otherwise
    the global CWD, or the original CWD as fallback.

    Returns:
        The current working directory
    """
    try:
        return pwd()
    except Exception:
        return get_original_cwd()


def change_cwd(cwd: str) -> None:
    """Change the current working directory.

    This updates both the process CWD and the global state.

    Args:
        cwd: The new working directory
    """
    os.chdir(cwd)
    set_global_cwd(cwd)
