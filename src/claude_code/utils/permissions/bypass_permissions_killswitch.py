"""
Bypass-permissions and auto-mode gate checks (``utils/permissions/bypassPermissionsKillswitch.ts``).

React hooks are omitted; call the async check functions from startup code.
``set_app_state`` matches ``(updater: (prev: dict) -> dict) -> None``.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from .permission_setup import (
    ToolPermissionContext,
    create_disabled_bypass_permissions_context,
    should_disable_bypass_permissions,
    verify_auto_mode_gate_access,
)

_bypass_ran = False
_auto_mode_ran = False


def _transcript_classifier_enabled() -> bool:
    return os.environ.get("CLAUDE_CODE_TRANSCRIPT_CLASSIFIER", "").lower() in ("1", "true", "yes")


async def check_and_disable_bypass_permissions_if_needed(
    tool_permission_context: ToolPermissionContext,
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
) -> None:
    global _bypass_ran
    if _bypass_ran:
        return
    _bypass_ran = True
    if not tool_permission_context.is_bypass_permissions_mode_available:
        return
    if not await __import__("asyncio").to_thread(should_disable_bypass_permissions):
        return

    def patch(prev: dict[str, Any]) -> dict[str, Any]:
        new_ctx = create_disabled_bypass_permissions_context(tool_permission_context)
        return {**prev, "tool_permission_context": new_ctx}

    set_app_state(patch)


def reset_bypass_permissions_check() -> None:
    global _bypass_ran
    _bypass_ran = False


async def check_and_disable_auto_mode_if_needed(
    tool_permission_context: ToolPermissionContext,
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
    fast_mode: bool | None = None,
) -> None:
    global _auto_mode_ran
    if _transcript_classifier_enabled():
        if _auto_mode_ran:
            return
        _auto_mode_ran = True
    update_ctx, notification = verify_auto_mode_gate_access(tool_permission_context, fast_mode)

    def patch(prev: dict[str, Any]) -> dict[str, Any]:
        prior_ctx = prev.get("tool_permission_context")
        base = prior_ctx if isinstance(prior_ctx, ToolPermissionContext) else tool_permission_context
        next_ctx = update_ctx(base)
        out: dict[str, Any] = {**prev, "tool_permission_context": next_ctx}
        if notification:
            n = dict(prev.get("notifications") or {})
            q = list(n.get("queue") or [])
            q.append(
                {
                    "key": "auto-mode-gate-notification",
                    "text": notification,
                    "color": "warning",
                    "priority": "high",
                }
            )
            n["queue"] = q
            out["notifications"] = n
        return out

    set_app_state(patch)


def reset_auto_mode_gate_check() -> None:
    global _auto_mode_ran
    _auto_mode_ran = False
