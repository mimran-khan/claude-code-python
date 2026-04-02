"""
Local /compact handler (lazy-loaded).

Migrated from: commands/compact/compact.ts

Full parity depends on services (session memory compaction, reactive compact,
microcompact, compactConversation, hooks). This module exposes the entry shape
expected by :class:`~claude_code.commands.spec.CommandSpec` ``load_symbol``.
"""

from __future__ import annotations

from typing import Any


async def call(
    args: str,
    *,
    messages: list[Any] | None = None,
    abort_controller: Any | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    """
    Mirror TypeScript ``LocalCommandCall`` result for type ``compact``.

    When the compaction stack is wired, replace the stub body with calls into
    ``claude_code.services.compact`` (or equivalent).
    """
    _ = abort_controller
    custom_instructions = (args or "").strip()
    if messages is not None and len(messages) == 0:
        raise RuntimeError("No messages to compact")

    return {
        "type": "compact",
        "compactionResult": {
            "stub": True,
            "customInstructions": custom_instructions or None,
        },
        "displayText": "Compacted (Python port — wire compaction services for full parity).",
    }


__all__ = ["call"]
