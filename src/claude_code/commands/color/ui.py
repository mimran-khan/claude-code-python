"""
/color local-jsx handler (session prompt bar color).

Migrated from: commands/color/color.ts
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

from claude_code.bootstrap.state import get_session_id
from claude_code.utils.agent_color_manager import AGENT_COLORS, AgentColorName
from claude_code.utils.session_storage import get_transcript_path, save_agent_color
from claude_code.utils.teammate_context import is_in_process_teammate

RESET_ALIASES: frozenset[str] = frozenset({"default", "reset", "none", "gray", "grey"})


def _color_list_text() -> str:
    return ", ".join(AGENT_COLORS) + ", default"


async def color_command_call(
    args: str,
    *,
    set_app_state: Callable[[Callable[[Any], Any]], None] | None = None,
) -> dict[str, str]:
    """
    Set or reset standalone session color; persists to transcript like TypeScript.

    Optional ``set_app_state`` may update host UI state (shape is host-defined).
    """
    if is_in_process_teammate():
        return {
            "type": "text",
            "value": (
                "Cannot set color: This session is a swarm teammate. Teammate colors are assigned by the team leader."
            ),
        }

    trimmed = (args or "").strip()
    if not trimmed:
        return {
            "type": "text",
            "value": f"Please provide a color. Available colors: {_color_list_text()}",
        }

    color_arg = trimmed.lower()
    session_id = str(get_session_id())
    transcript_path = get_transcript_path(session_id)

    if color_arg in RESET_ALIASES:
        save_agent_color(session_id, "default", transcript_path=transcript_path)
        if set_app_state is not None:

            def _clear(prev: Any) -> Any:
                sac = getattr(prev, "standalone_agent_context", None)
                if sac is None:
                    return prev
                name = getattr(sac, "name", "") or ""
                if hasattr(prev, "model_copy"):

                    class _Patch:
                        pass

                    new_sac = sac.model_copy(update={"name": name, "color": None})
                    return prev.model_copy(
                        update={"standalone_agent_context": new_sac},
                    )
                new_sac = {**sac, "name": name, "color": None} if isinstance(sac, dict) else sac
                return {**prev, "standalone_agent_context": new_sac} if isinstance(prev, dict) else prev

            with contextlib.suppress(Exception):
                set_app_state(_clear)
        return {"type": "text", "value": "Session color reset to default"}

    if color_arg not in AGENT_COLORS:
        return {
            "type": "text",
            "value": (f'Invalid color "{color_arg}". Available colors: {_color_list_text()}'),
        }

    save_agent_color(session_id, color_arg, transcript_path=transcript_path)
    chosen: AgentColorName = color_arg  # type: ignore[assignment]

    if set_app_state is not None:

        def _set(prev: Any) -> Any:
            sac = getattr(prev, "standalone_agent_context", None)
            if sac is None:
                return prev
            name = getattr(sac, "name", "") or ""
            if hasattr(prev, "model_copy"):
                new_sac = sac.model_copy(
                    update={"name": name, "color": chosen},
                )
                return prev.model_copy(
                    update={"standalone_agent_context": new_sac},
                )
            new_sac = {**sac, "name": name, "color": chosen} if isinstance(sac, dict) else sac
            return {**prev, "standalone_agent_context": new_sac} if isinstance(prev, dict) else prev

        with contextlib.suppress(Exception):
            set_app_state(_set)

    return {"type": "text", "value": f"Session color set to: {color_arg}"}


# TS default export shape: module with ``call`` for lazy load.
call = color_command_call

__all__ = ["call", "color_command_call", "RESET_ALIASES"]
