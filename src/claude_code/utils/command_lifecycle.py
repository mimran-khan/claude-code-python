"""
Command lifecycle notifications (started / completed).

Migrated from: utils/commandLifecycle.ts
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

CommandLifecycleState = Literal["started", "completed"]
CommandLifecycleListener = Callable[[str, CommandLifecycleState], None]

_listener: CommandLifecycleListener | None = None


def set_command_lifecycle_listener(cb: CommandLifecycleListener | None) -> None:
    """Register or clear the global listener for command lifecycle events."""
    global _listener
    _listener = cb


def notify_command_lifecycle(uuid: str, state: CommandLifecycleState) -> None:
    """Invoke the registered listener, if any."""
    if _listener is not None:
        _listener(uuid, state)
