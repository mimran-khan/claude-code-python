"""
/brief local-jsx entry (toggle brief-only mode).

Migrated from: commands/brief.ts
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

from claude_code.bootstrap.state import (
    get_kairos_active,
    get_user_msg_opt_in,
    set_user_msg_opt_in,
)
from claude_code.services.analytics.events import log_event
from claude_code.tools.brief_tool.brief_tool import BRIEF_TOOL_NAME, is_brief_entitled


def _read_brief_only(context: Any | None) -> bool:
    if context is None:
        return get_user_msg_opt_in()
    gas = getattr(context, "get_app_state", None)
    if callable(gas):
        try:
            st = gas()
            if hasattr(st, "is_brief_only"):
                return bool(st.is_brief_only)
            if isinstance(st, dict) and "is_brief_only" in st:
                return bool(st["is_brief_only"])
        except Exception:
            pass
    return get_user_msg_opt_in()


async def call(
    _args: str,
    *,
    context: Any = None,
    set_app_state: Callable[[Callable[[Any], Any]], None] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Toggle brief-only mode; mirrors TypeScript ``brief.call`` result shape.

    The interactive host may pass ``set_app_state`` to update UI state.
    """
    _ = kwargs
    current = _read_brief_only(context)
    new_state = not current

    if new_state and not is_brief_entitled():
        log_event(
            "tengu_brief_mode_toggled",
            {"enabled": False, "gated": True, "source": "slash_command"},
        )
        return {
            "type": "done",
            "message": "Brief tool is not enabled for your account",
            "display": "system",
        }

    set_user_msg_opt_in(new_state)

    if set_app_state is not None:

        def _patch(prev: Any) -> Any:
            if hasattr(prev, "model_copy"):
                return prev.model_copy(update={"is_brief_only": new_state})
            if isinstance(prev, dict):
                return {**prev, "is_brief_only": new_state}
            return prev

        with contextlib.suppress(Exception):
            set_app_state(_patch)

    log_event(
        "tengu_brief_mode_toggled",
        {"enabled": new_state, "gated": False, "source": "slash_command"},
    )

    meta_messages: list[str] | None = None
    if not get_kairos_active():
        if new_state:
            reminder = (
                f"Brief mode is now enabled. Use the {BRIEF_TOOL_NAME} tool for all "
                "user-facing output — plain text outside it is hidden from the user's view."
            )
        else:
            reminder = (
                f"Brief mode is now disabled. The {BRIEF_TOOL_NAME} tool is no longer "
                "available — reply with plain text."
            )
        meta_messages = [f"<system-reminder>\n{reminder}\n</system-reminder>"]

    return {
        "type": "done",
        "message": "Brief-only mode enabled" if new_state else "Brief-only mode disabled",
        "display": "system",
        "metaMessages": meta_messages,
    }


__all__ = ["call"]
