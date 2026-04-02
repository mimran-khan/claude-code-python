"""
Diff hook after AppState updates (permission mode sync, etc.).

Migrated from: state/onChangeAppState.ts (reduced — wire real notifiers at integration).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .app_state import AppState

NotifySessionMetadata = Callable[[dict[str, Any]], None]
NotifyPermissionMode = Callable[[Any], None]


@dataclass
class AppStateChangeHooks:
    """Optional out-of-band notifications (CCR, SDK streams)."""

    notify_session_metadata: NotifySessionMetadata | None = None
    notify_permission_mode_changed: NotifyPermissionMode | None = None


_hooks = AppStateChangeHooks()


def set_app_state_change_hooks(hooks: AppStateChangeHooks) -> None:
    """Install global hooks (call from CLI / headless bootstrap)."""
    global _hooks
    _hooks = hooks


def external_metadata_to_app_state(metadata: dict[str, Any]) -> Callable[[AppState], AppState]:
    """Build updater from CCR ``external_metadata`` snapshot."""

    def updater(prev: AppState) -> AppState:
        from dataclasses import replace

        next_ctx = dict(prev.tool_permission_context or {})
        if isinstance(metadata.get("permission_mode"), str):
            next_ctx["mode"] = metadata["permission_mode"]
        next_state = replace(prev, tool_permission_context=next_ctx)
        if isinstance(metadata.get("is_ultraplan_mode"), bool):
            next_state = replace(next_state, is_ultraplan_mode=metadata["is_ultraplan_mode"])
        return next_state

    return updater


def on_change_app_state(*, new_state: AppState, old_state: AppState) -> None:
    """Invoke side effects when state changes (permission mode, etc.)."""
    prev_mode = (old_state.tool_permission_context or {}).get("mode")
    new_mode = (new_state.tool_permission_context or {}).get("mode")
    if prev_mode != new_mode:
        if _hooks.notify_permission_mode_changed is not None:
            _hooks.notify_permission_mode_changed(new_mode)
        if _hooks.notify_session_metadata is not None:
            _hooks.notify_session_metadata({"permission_mode": new_mode})
    if new_state.main_loop_model != old_state.main_loop_model and new_state.main_loop_model is None:
        from ..utils.settings import update_settings_for_source

        update_settings_for_source("userSettings", {"model": None})
