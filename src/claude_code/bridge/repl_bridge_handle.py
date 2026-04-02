"""Global REPL bridge handle pointer (ported from bridge/replBridgeHandle.ts)."""

from __future__ import annotations

from typing import Any

from claude_code.bridge.session_id_compat import to_compat_session_id

_handle: Any | None = None


def set_repl_bridge_handle(h: Any | None) -> None:
    global _handle
    _handle = h


def get_repl_bridge_handle() -> Any | None:
    return _handle


def get_self_bridge_compat_id() -> str | None:
    h = get_repl_bridge_handle()
    if not h:
        return None
    sid = getattr(h, "bridge_session_id", None)
    if not isinstance(sid, str):
        return None
    return to_compat_session_id(sid)
