"""
Combined cancellation: parent events + optional timeout.

Migrated from: utils/combinedAbortSignal.ts

Uses threading primitives so setup works outside a running asyncio loop (mirrors
sync AbortController wiring in Node). For asyncio-only code, prefer ``asyncio.wait_for``.
"""

from __future__ import annotations

import threading
from collections.abc import Callable


def create_combined_abort_signal(
    signal: threading.Event | None = None,
    *,
    signal_b: threading.Event | None = None,
    timeout_ms: int | None = None,
) -> tuple[threading.Event, Callable[[], None]]:
    """
    Return (combined_event, cleanup). ``combined_event`` is set when any input
    is set or after ``timeout_ms``.
    """
    combined = threading.Event()
    timer: threading.Timer | None = None

    def fire() -> None:
        combined.set()
        if timer is not None:
            timer.cancel()

    if (signal is not None and signal.is_set()) or (signal_b is not None and signal_b.is_set()):
        combined.set()
        return combined, lambda: None

    def wait_and_fire(ev: threading.Event) -> None:
        ev.wait()
        fire()

    for ev in (signal, signal_b):
        if ev is None:
            continue
        threading.Thread(target=wait_and_fire, args=(ev,), daemon=True).start()

    if timeout_ms is not None:

        def on_timeout() -> None:
            fire()

        timer = threading.Timer(timeout_ms / 1000.0, on_timeout)
        timer.daemon = True
        timer.start()

    def cleanup() -> None:
        if timer is not None:
            timer.cancel()

    return combined, cleanup
