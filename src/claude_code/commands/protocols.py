"""
Protocols for lazily wired command dependencies.

Migrated from: bridge/bridgeDebug.ts (bridge-kick), Tool.js, etc.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol

FaultKind = Literal["transient", "fatal"]


class BridgeDebugHandle(Protocol):
    """Injected bridge fault surface for ant-only /bridge-kick testing."""

    def fire_close(self, code: int) -> None: ...

    def inject_fault(self, fault: dict[str, Any]) -> None: ...

    def wake_poll_loop(self) -> None: ...

    def force_reconnect(self) -> None: ...

    def describe(self) -> str: ...


_bridge_debug_handle: BridgeDebugHandle | None = None


def register_bridge_debug_handle(handle: BridgeDebugHandle | None) -> None:
    """Called from bridge bootstrap when debug tooling is available."""
    global _bridge_debug_handle
    _bridge_debug_handle = handle


def get_bridge_debug_handle() -> BridgeDebugHandle | None:
    return _bridge_debug_handle
