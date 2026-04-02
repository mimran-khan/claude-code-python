"""
Permission / auto-mode gating (stub core of ``utils/permissions/permissionSetup.ts``).

Feature flags and Statsig hooks from the TypeScript UI are not wired here; env
vars provide local overrides for headless / SDK use.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any


@dataclass
class ToolPermissionContext:
    """Minimal stand-in for the React ``ToolPermissionContext`` (snake_case fields)."""

    mode: str
    is_bypass_permissions_mode_available: bool = False
    is_auto_mode_available: bool = False


def is_auto_mode_gate_enabled() -> bool:
    return os.environ.get("CLAUDE_CODE_AUTO_MODE_GATE", "").lower() in ("1", "true", "yes")


def get_auto_mode_unavailable_reason() -> str:
    if not is_auto_mode_gate_enabled():
        return "gate_disabled"
    return "unknown"


def get_auto_mode_enabled_state() -> str:
    """
    Rough parity with TS ``getAutoModeEnabledState`` (feature / product config).

    Override with ``CLAUDE_CODE_AUTO_MODE_ENABLED_STATE=enabled|opt-in|disabled``.
    When unset and the auto-mode gate env is on, treats config as ``enabled``.
    """
    raw = os.environ.get("CLAUDE_CODE_AUTO_MODE_ENABLED_STATE", "").strip().lower()
    if raw in ("enabled", "opt-in", "disabled"):
        return raw
    if is_auto_mode_gate_enabled():
        return "enabled"
    return "opt-in"


def should_disable_bypass_permissions() -> bool:
    return os.environ.get("CLAUDE_CODE_DISABLE_BYPASS_PERMISSIONS", "").lower() in (
        "1",
        "true",
        "yes",
    )


def create_disabled_bypass_permissions_context(
    ctx: ToolPermissionContext,
) -> ToolPermissionContext:
    return replace(ctx, is_bypass_permissions_mode_available=False)


def verify_auto_mode_gate_access(
    ctx: ToolPermissionContext,
    fast_mode: bool | None = None,
) -> tuple[Callable[[ToolPermissionContext], ToolPermissionContext], str | None]:
    _ = fast_mode

    def update_context(prev: ToolPermissionContext) -> ToolPermissionContext:
        if not is_auto_mode_gate_enabled():
            return replace(prev, is_auto_mode_available=False)
        return prev

    note = None
    if not is_auto_mode_gate_enabled():
        note = "Auto mode is disabled for this build (CLAUDE_CODE_AUTO_MODE_GATE)."
    return update_context, note


def transition_permission_mode(
    ctx: ToolPermissionContext,
    new_mode: str,
) -> ToolPermissionContext:
    return replace(ctx, mode=new_mode)


def apply_app_state_tool_context(
    prev: dict[str, Any],
    new_ctx: ToolPermissionContext,
) -> dict[str, Any]:
    tpc = dict(prev.get("tool_permission_context") or {})
    tpc.update(
        mode=new_ctx.mode,
        is_bypass_permissions_mode_available=new_ctx.is_bypass_permissions_mode_available,
        is_auto_mode_available=new_ctx.is_auto_mode_available,
    )
    return {**prev, "tool_permission_context": tpc}
