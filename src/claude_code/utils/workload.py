"""
Workload Context Utilities.

Turn-scoped workload tag via context variables.
"""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from typing import TypeVar

T = TypeVar("T")


# Context variable for workload
_workload_context: ContextVar[str | None] = ContextVar("workload", default=None)


# Workload type constant
WORKLOAD_CRON = "cron"


def get_workload() -> str | None:
    """Get the current workload tag.

    Returns:
        The workload tag or None
    """
    return _workload_context.get()


def run_with_workload(workload: str | None, fn: Callable[[], T]) -> T:
    """Run a function with a workload context.

    Always establishes a new context boundary, even when workload is None.

    Args:
        workload: The workload tag
        fn: The function to run

    Returns:
        The function result
    """
    token = _workload_context.set(workload)
    try:
        return fn()
    finally:
        _workload_context.reset(token)


def set_workload(workload: str | None) -> None:
    """Set the workload for the current context.

    Args:
        workload: The workload tag
    """
    _workload_context.set(workload)
