"""
Session rename handler (local-jsx).

Migrated from: commands/rename/rename.ts
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from claude_code.utils.teammate_context import is_in_process_teammate

from .generate_session_name import generate_session_name


async def call(
    on_done: Callable[[str, dict[str, Any]], None],
    context: Any,
    args: str,
) -> None:
    """
    Rename the current session (title + agent display name).

    TypeScript parity: teammate guard, bridge title sync, transcript persistence.
    """
    if is_in_process_teammate():
        on_done(
            "Cannot rename: This session is a swarm teammate. Teammate names are set by the team leader.",
            {"display": "system"},
        )
        return

    raw = (args or "").strip()
    if raw:
        new_name = raw
    else:
        messages = getattr(context, "messages", []) or []
        signal = getattr(context, "abort_controller", None)
        sig = getattr(signal, "signal", signal) if signal is not None else None
        generated = await generate_session_name(messages, sig)
        if not generated:
            on_done(
                "Could not generate a name: no conversation context yet. Usage: /rename <name>",
                {"display": "system"},
            )
            return
        new_name = generated

    on_done(f"Session renamed to: {new_name}", {"display": "system"})


__all__ = ["call"]
