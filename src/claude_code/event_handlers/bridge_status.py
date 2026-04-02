"""Bridge footer / indicator status (ported from bridge/bridgeStatusUtil.ts)."""

from __future__ import annotations

from claude_code.bridge.bridge_status_util import (
    BridgeStatusInfo,
    get_bridge_status,
)

__all__ = ["BridgeStatusInfo", "get_bridge_status", "bridge_status_snapshot"]


def bridge_status_snapshot(
    *,
    error: str | None,
    connected: bool,
    session_active: bool,
    reconnecting: bool,
) -> BridgeStatusInfo:
    """Thin alias for tests and call sites that prefer a verb over get_bridge_status."""
    return get_bridge_status(
        error=error,
        connected=connected,
        session_active=session_active,
        reconnecting=reconnecting,
    )
