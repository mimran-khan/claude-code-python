"""
Shift+Tab permission mode cycling (``utils/permissions/getNextPermissionMode.ts``).
"""

from __future__ import annotations

import os

from ..debug import log_for_debugging
from .permission_mode import PermissionMode
from .permission_setup import (
    ToolPermissionContext,
    get_auto_mode_unavailable_reason,
    is_auto_mode_gate_enabled,
)


def _transcript_classifier_enabled() -> bool:
    return os.environ.get("CLAUDE_CODE_TRANSCRIPT_CLASSIFIER", "").lower() in ("1", "true", "yes")


def can_cycle_to_auto(ctx: ToolPermissionContext) -> bool:
    if not _transcript_classifier_enabled():
        return False
    gate = is_auto_mode_gate_enabled()
    can = bool(ctx.is_auto_mode_available and gate)
    if not can:
        log_for_debugging(
            "[auto-mode] can_cycle_to_auto=false: "
            f"ctx.is_auto_mode_available={ctx.is_auto_mode_available} "
            f"is_auto_mode_gate_enabled={gate} reason={get_auto_mode_unavailable_reason()}",
        )
    return can


def get_next_permission_mode(
    tool_permission_context: ToolPermissionContext,
    _team_context: dict[str, str] | None = None,
) -> PermissionMode:
    mode = tool_permission_context.mode
    if mode == "default":
        if os.environ.get("USER_TYPE") == "ant":
            if tool_permission_context.is_bypass_permissions_mode_available:
                return "bypassPermissions"
            if can_cycle_to_auto(tool_permission_context):
                return "auto"
            return "default"
        return "acceptEdits"
    if mode == "acceptEdits":
        return "plan"
    if mode == "plan":
        if tool_permission_context.is_bypass_permissions_mode_available:
            return "bypassPermissions"
        if can_cycle_to_auto(tool_permission_context):
            return "auto"
        return "default"
    if mode == "bypassPermissions":
        if can_cycle_to_auto(tool_permission_context):
            return "auto"
        return "default"
    if mode == "dontAsk":
        return "default"
    return "default"
