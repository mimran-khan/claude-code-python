"""
Turn-end cleanup for computer-use MCP (unhide + lock + escape hotkey).

Migrated from: utils/computerUse/cleanup.ts
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from ..debug import log_for_debugging
from .esc_hotkey import unregister_esc_hotkey
from .executor import unhide_computer_use_apps
from .lock import is_lock_held_locally, release_computer_use_lock

_UNHIDE_TIMEOUT_S = 5.0


class ComputerUseCleanupContext(Protocol):
    def get_app_state(self) -> Any: ...

    def set_app_state(self, updater: Any) -> None: ...

    def send_os_notification(self, payload: dict[str, Any]) -> None: ...


def _get_hidden_during_turn(state: Any) -> set[str] | None:
    mcp = getattr(state, "computer_use_mcp_state", None)
    if mcp is None:
        return None
    raw = getattr(mcp, "hidden_during_turn", None)
    if raw is None:
        return None
    if isinstance(raw, set):
        return raw
    try:
        return set(raw)
    except TypeError:
        return None


async def cleanup_computer_use_after_turn(ctx: ComputerUseCleanupContext) -> None:
    state = ctx.get_app_state()
    hidden = _get_hidden_during_turn(state)
    if hidden and len(hidden) > 0:
        try:
            await asyncio.wait_for(unhide_computer_use_apps(list(hidden)), timeout=_UNHIDE_TIMEOUT_S)
        except Exception as e:
            log_for_debugging(f"[Computer Use MCP] auto-unhide failed: {e}")

    if not is_lock_held_locally():
        return

    try:
        unregister_esc_hotkey()
    except Exception as e:
        log_for_debugging(f"[Computer Use MCP] unregister_esc_hotkey failed: {e}")

    if await release_computer_use_lock():
        send = getattr(ctx, "send_os_notification", None) or getattr(ctx, "sendOSNotification", None)
        if callable(send):
            try:
                send(
                    {
                        "message": "Claude is done using your computer",
                        "notificationType": "computer_use_exit",
                    },
                )
            except Exception:
                pass
