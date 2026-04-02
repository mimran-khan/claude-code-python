"""
Async wrapper with timeout (replaces macOS CFRunLoop pump from drainRunLoop.ts).

Native Swift/input queues do not exist in the Python port; ``drain_run_loop`` uses
``asyncio.wait_for``. ``retain_pump`` / ``release_pump`` share a refcount for API
parity with the TypeScript Escape hotkey + drain lifecycle.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from ..debug import log_for_debugging

T = TypeVar("T")

_TIME_OUT_S = 30.0
_pump_depth = 0


def retain_pump() -> None:
    """Increment pump refcount (no CFRunLoop in Python; logs at depth transitions)."""
    global _pump_depth
    _pump_depth += 1
    if _pump_depth == 1:
        log_for_debugging("[drain_run_loop] pump retain (python shim)", level="verbose")


def release_pump() -> None:
    global _pump_depth
    _pump_depth = max(0, _pump_depth - 1)
    if _pump_depth == 0:
        log_for_debugging("[drain_run_loop] pump release (python shim)", level="verbose")


async def drain_run_loop(fn: Callable[[], Awaitable[T]], *, timeout_s: float = _TIME_OUT_S) -> T:
    """Run ``fn()`` under a per-call timeout. Safe to nest."""
    retain_pump()
    try:
        return await asyncio.wait_for(fn(), timeout=timeout_s)
    finally:
        release_pump()
