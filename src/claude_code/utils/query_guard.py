"""
Query lifecycle guard (migrated from ``utils/QueryGuard.ts``).

Mirrors the TS state machine for queue / single-flight query handling.
"""

from __future__ import annotations

from collections.abc import Callable

from claude_code.utils.signal import create_signal


class QueryGuard:
    """idle | dispatching | running — synchronous transitions (React parity)."""

    __slots__ = ("_status", "_generation", "_changed")

    def __init__(self) -> None:
        self._status: str = "idle"
        self._generation = 0
        self._changed = create_signal()

    def reserve(self) -> bool:
        if self._status != "idle":
            return False
        self._status = "dispatching"
        self._notify()
        return True

    def cancel_reservation(self) -> None:
        if self._status != "dispatching":
            return
        self._status = "idle"
        self._notify()

    def try_start(self) -> int | None:
        if self._status == "running":
            return None
        self._status = "running"
        self._generation += 1
        self._notify()
        return self._generation

    def end(self, generation: int) -> bool:
        if self._generation != generation or self._status != "running":
            return False
        self._status = "idle"
        self._notify()
        return True

    def force_end(self) -> None:
        if self._status == "idle":
            return
        self._status = "idle"
        self._generation += 1
        self._notify()

    @property
    def is_active(self) -> bool:
        return self._status != "idle"

    @property
    def generation(self) -> int:
        return self._generation

    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        return self._changed.subscribe(listener)

    def get_snapshot(self) -> bool:
        return self._status != "idle"

    def _notify(self) -> None:
        self._changed.emit()


__all__ = ["QueryGuard"]
