"""
/clear local handler.

Migrated from: commands/clear/clear.ts
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from claude_code.core.tool import FileStateCache

from .conversation import ClearConversationParams, clear_conversation


async def clear_command_call(
    _args: str,
    *,
    set_messages: Callable[[Callable[[list[Any]], list[Any]]], None],
    read_file_state: FileStateCache,
    get_app_state: Callable[[], Any] | None = None,
    set_app_state: Callable[[Callable[[Any], Any]], None] | None = None,
    set_conversation_id: Callable[[Any], None] | None = None,
) -> dict[str, str]:
    await clear_conversation(
        ClearConversationParams(
            set_messages=set_messages,
            read_file_state=read_file_state,
            get_app_state=get_app_state,
            set_app_state=set_app_state,
            set_conversation_id=set_conversation_id,
        )
    )
    return {"type": "text", "value": ""}


__all__ = ["clear_command_call"]
